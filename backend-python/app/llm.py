"""LLM client module.

Provides a shared Google Gemini client for the application.
Used by both Graphiti and direct LLM calls for response generation.
"""

import os
import logging
from typing import Optional

from google import genai

from .config import get_settings

logger = logging.getLogger(__name__)

# Singleton client instances
_client: Optional[genai.Client] = None
_global_client: Optional[genai.Client] = None  # For gemini-3 models that require global endpoint


def _is_gemini3_model(model_name: str) -> bool:
    """Check if model requires global endpoint (gemini-3 models)."""
    return model_name.startswith("gemini-3")


def get_gemini_client(model: Optional[str] = None) -> genai.Client:
    """Get or create the shared Gemini client.

    Args:
        model: Optional model name. If gemini-3 model, returns global endpoint client.

    Returns:
        Configured genai.Client instance
    """
    global _client, _global_client

    settings = get_settings()
    api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY", "")

    # For API key auth, same client works for all models
    if api_key:
        if _client is None:
            logger.info("Initializing Gemini client with API key")
            _client = genai.Client(api_key=api_key)
        return _client

    # For Vertex AI, gemini-3 models need global endpoint
    use_global = model and _is_gemini3_model(model)

    if use_global:
        if _global_client is None:
            logger.info("Initializing Gemini client with Vertex AI (global endpoint for gemini-3)")
            if settings.google_application_credentials:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
            _global_client = genai.Client(
                vertexai=True,
                project=settings.vertex_ai_project_id,
                location="global",
            )
        return _global_client
    else:
        if _client is None:
            logger.info("Initializing Gemini client with Vertex AI")
            if settings.google_application_credentials:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
            _client = genai.Client(
                vertexai=True,
                project=settings.vertex_ai_project_id,
                location=settings.vertex_ai_location,
            )
        return _client


async def generate_text(
    prompt: str,
    model: Optional[str] = None,
) -> str:
    """Generate text using Gemini.

    Args:
        prompt: The prompt to send to the model
        model: Model name (default: from settings)

    Returns:
        Generated text response
    """
    settings = get_settings()
    model_name = model or settings.llm_model
    client = get_gemini_client(model=model_name)

    try:
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Failed to generate text: {e}")
        raise


def close_client() -> None:
    """Close the Gemini clients (cleanup on shutdown)."""
    global _client, _global_client
    _client = None
    _global_client = None
    logger.info("Gemini clients closed")
