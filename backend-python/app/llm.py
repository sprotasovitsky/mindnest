"""LLM client module.

Provides a shared Google Gemini client for the application.
Used by both Graphiti and direct LLM calls for response generation.

Observability:
- structlog JSON logging for every call (latency, tokens, cost)
- Prometheus metrics: llm_request_duration_seconds, llm_tokens_total, llm_cost_usd_total
- Langfuse generation spans (when LANGFUSE_PUBLIC_KEY is set)
"""

import asyncio
import time
from typing import Optional

import structlog
from google import genai
from google.genai import types
from google.oauth2 import service_account

from .config import get_settings

logger = structlog.get_logger(__name__)

# Singleton client instances
_client: Optional[genai.Client] = None
_global_client: Optional[genai.Client] = None  # For gemini-3 models that require global endpoint
_credentials: Optional[service_account.Credentials] = None

# Gemini pricing per token in USD
# Source: docs/observability-plan.md
GEMINI_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-flash-lite":  {"input": 0.000_000_075, "output": 0.000_000_3},
    "gemini-2.5-flash":       {"input": 0.000_000_15,  "output": 0.000_000_6},
    "gemini-3-flash-preview": {"input": 0.000_000_075, "output": 0.000_000_3},
}


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for a LLM call."""
    pricing = GEMINI_PRICING.get(model)
    if not pricing:
        return 0.0
    return input_tokens * pricing["input"] + output_tokens * pricing["output"]


def _is_gemini3_model(model_name: str) -> bool:
    """Check if model requires global endpoint (gemini-3 models)."""
    return model_name.startswith("gemini-3")


def _get_vertex_credentials() -> Optional[service_account.Credentials]:
    """Get Vertex AI credentials from env vars."""
    global _credentials

    if _credentials is not None:
        return _credentials

    settings = get_settings()

    if not settings.gcp_service_account_email or not settings.gcp_private_key:
        return None

    # Replace literal \n with actual newlines in private key
    private_key = settings.gcp_private_key.replace("\\n", "\n")

    _credentials = service_account.Credentials.from_service_account_info(
        {
            "type": "service_account",
            "project_id": settings.vertex_ai_project_id,
            "private_key": private_key,
            "client_email": settings.gcp_service_account_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        },
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return _credentials


def get_gemini_client(model: Optional[str] = None) -> genai.Client:
    """Get or create the shared Gemini client.

    Args:
        model: Optional model name. If gemini-3 model, returns global endpoint client.

    Returns:
        Configured genai.Client instance
    """
    global _client, _global_client

    settings = get_settings()

    # Get credentials from env vars
    credentials = _get_vertex_credentials()
    if not credentials:
        raise ValueError(
            "Vertex AI credentials required. Set GCP_SERVICE_ACCOUNT_EMAIL, "
            "GCP_PRIVATE_KEY, and VERTEX_AI_PROJECT_ID environment variables."
        )

    # gemini-3 models need global endpoint
    use_global = model and _is_gemini3_model(model)

    if use_global:
        if _global_client is None:
            logger.info("Initializing Gemini client with Vertex AI (global endpoint for gemini-3)")
            _global_client = genai.Client(
                vertexai=True,
                project=settings.vertex_ai_project_id,
                location="global",
                credentials=credentials,
            )
        return _global_client
    else:
        if _client is None:
            logger.info("Initializing Gemini client with Vertex AI")
            _client = genai.Client(
                vertexai=True,
                project=settings.vertex_ai_project_id,
                location=settings.vertex_ai_location,
                credentials=credentials,
            )
        return _client


_RETRY_DELAYS = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s


async def generate_text(
    prompt: str,
    model: Optional[str] = None,
    prompt_name: Optional[str] = None,
    step: Optional[str] = None,
    trace_id: Optional[str] = None,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """Generate text using Gemini with retry on transient errors.

    Args:
        prompt: The prompt to send to the model
        model: Model name (default: from settings)
        prompt_name: Prompt template name for observability (e.g. "classifier", "response")
        step: Pipeline step for observability (e.g. "classify", "chat_response")
        trace_id: Request-level trace ID to correlate all LLM calls in one request
        project_id: Project ID for observability context
        user_id: User ID for observability context

    Returns:
        Generated text response
    """
    from .metrics import llm_latency, llm_tokens, llm_cost, llm_errors
    from .langfuse_client import get_langfuse

    settings = get_settings()
    model_name = model or settings.llm_model
    client = get_gemini_client(model=model_name)
    step_label = step or "unknown"

    # Open Langfuse generation span
    lf = get_langfuse()
    generation = None
    if lf and trace_id:
        try:
            generation = lf.generation(
                name=step_label,
                model=model_name,
                input=prompt,
                trace_id=trace_id,
                metadata={
                    "prompt_name": prompt_name,
                    "project_id": project_id,
                    "user_id": user_id,
                },
            )
        except Exception:
            generation = None

    last_error: Optional[Exception] = None
    t_start = time.monotonic()

    for attempt in range(len(_RETRY_DELAYS) + 1):
        try:
            # Enable thinking for 3.1+ models
            config = None
            if model_name.startswith("gemini-3"):
                thinking_level = settings.llm_thinking_level
                thinking_cfg = types.ThinkingConfig(thinking_level=thinking_level) if thinking_level != "NONE" else None
                max_tokens = settings.llm_max_output_tokens or None
                config = types.GenerateContentConfig(
                    thinking_config=thinking_cfg,
                    max_output_tokens=max_tokens,
                )
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            text = response.text
            latency_ms = int((time.monotonic() - t_start) * 1000)

            # Extract token counts
            input_tokens = 0
            output_tokens = 0
            thinking_tokens = 0
            usage = getattr(response, "usage_metadata", None)
            if usage:
                input_tokens = getattr(usage, "prompt_token_count", 0) or 0
                output_tokens = getattr(usage, "candidates_token_count", 0) or 0
                thinking_tokens = getattr(usage, "thoughts_token_count", 0) or 0

            cost_usd = _calculate_cost(model_name, input_tokens, output_tokens)

            # Prometheus
            llm_latency.labels(model=model_name, step=step_label).observe(latency_ms / 1000)
            if input_tokens:
                llm_tokens.labels(model=model_name, token_type="input").inc(input_tokens)
            if output_tokens:
                llm_tokens.labels(model=model_name, token_type="output").inc(output_tokens)
            if thinking_tokens:
                llm_tokens.labels(model=model_name, token_type="thinking").inc(thinking_tokens)
            if cost_usd:
                llm_cost.labels(model=model_name, step=step_label).inc(cost_usd)

            # Structured log
            log_kwargs: dict = dict(
                model=model_name,
                step=step_label,
                prompt_name=prompt_name,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=round(cost_usd, 8) if cost_usd else None,
                trace_id=trace_id,
                project_id=project_id,
            )
            if thinking_tokens:
                log_kwargs["thinking_tokens"] = thinking_tokens

            if not text or not text.strip():
                logger.warning("llm_empty_response", **log_kwargs)
            else:
                logger.info("llm_call", **log_kwargs)

            # Close Langfuse span
            if generation:
                try:
                    generation.end(
                        output=text or "",
                        usage={
                            "input": input_tokens,
                            "output": output_tokens,
                            "total": input_tokens + output_tokens + thinking_tokens,
                        },
                    )
                except Exception:
                    pass

            return text or ""

        except Exception as e:
            last_error = e
            if attempt < len(_RETRY_DELAYS):
                delay = _RETRY_DELAYS[attempt]
                logger.warning(
                    "llm_retry",
                    model=model_name,
                    step=step_label,
                    attempt=attempt + 1,
                    max_attempts=len(_RETRY_DELAYS) + 1,
                    delay_s=delay,
                    error=str(e),
                )
                await asyncio.sleep(delay)
            else:
                latency_ms = int((time.monotonic() - t_start) * 1000)
                logger.error(
                    "llm_failed",
                    model=model_name,
                    step=step_label,
                    prompt_name=prompt_name,
                    latency_ms=latency_ms,
                    error=str(e),
                    trace_id=trace_id,
                )
                llm_errors.labels(model=model_name, step=step_label).inc()

                if generation:
                    try:
                        generation.end(output=None, level="ERROR", status_message=str(e))
                    except Exception:
                        pass

    raise last_error  # type: ignore[misc]


def close_client() -> None:
    """Close the Gemini clients (cleanup on shutdown)."""
    global _client, _global_client
    _client = None
    _global_client = None
    logger.info("gemini_clients_closed")
