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

# Singleton client instance
_client: Optional[genai.Client] = None


def get_gemini_client() -> genai.Client:
    """Get or create the shared Gemini client.

    Returns:
        Configured genai.Client instance
    """
    global _client

    if _client is not None:
        return _client

    settings = get_settings()
    api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY", "")

    if api_key:
        logger.info("Initializing Gemini client with API key")
        _client = genai.Client(api_key=api_key)
    else:
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
    client = get_gemini_client()
    model_name = model or settings.llm_model

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
    """Close the Gemini client (cleanup on shutdown)."""
    global _client
    _client = None
    logger.info("Gemini client closed")
