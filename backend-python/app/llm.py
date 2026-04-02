"""LLM client module.

Provides a shared Google Gemini client for the application.
Used by both Graphiti and direct LLM calls for response generation.
"""

import asyncio
import logging
from typing import Optional

from google import genai
from google.genai import types
from google.oauth2 import service_account

from .config import get_settings

logger = logging.getLogger(__name__)

# Singleton client instances
_client: Optional[genai.Client] = None
_global_client: Optional[genai.Client] = None  # For gemini-3 models that require global endpoint
_credentials: Optional[service_account.Credentials] = None


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
) -> str:
    """Generate text using Gemini with retry on transient errors.

    Args:
        prompt: The prompt to send to the model
        model: Model name (default: from settings)

    Returns:
        Generated text response
    """
    settings = get_settings()
    model_name = model or settings.llm_model
    client = get_gemini_client(model=model_name)

    last_error: Optional[Exception] = None
    for attempt in range(len(_RETRY_DELAYS) + 1):
        try:
            # Enable thinking for 3.1+ models
            config = None
            if model_name.startswith("gemini-3"):
                config = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=1024),
                )
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            text = response.text
            if not text or not text.strip():
                logger.warning(f"LLM returned empty response. Candidates: {response.candidates}")
            return text or ""
        except Exception as e:
            last_error = e
            if attempt < len(_RETRY_DELAYS):
                delay = _RETRY_DELAYS[attempt]
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{len(_RETRY_DELAYS) + 1}), "
                    f"retrying in {delay}s: {e}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"LLM call failed after {len(_RETRY_DELAYS) + 1} attempts: {e}")

    raise last_error  # type: ignore[misc]


def close_client() -> None:
    """Close the Gemini clients (cleanup on shutdown)."""
    global _client, _global_client
    _client = None
    _global_client = None
    logger.info("Gemini clients closed")
