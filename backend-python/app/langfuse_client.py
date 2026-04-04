"""Langfuse client singleton for LLM observability.

Provides a shared Langfuse client for tracing LLM calls.
Returns None gracefully if Langfuse is not configured.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_langfuse = None


def get_langfuse():
    """Get or create the shared Langfuse client.

    Returns None if LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY are not set,
    so all call sites can do: `if lf := get_langfuse(): ...`
    """
    global _langfuse

    if _langfuse is not None:
        return _langfuse

    from .config import get_settings
    settings = get_settings()

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None

    try:
        from langfuse import Langfuse
        _langfuse = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        logger.info(f"Langfuse client initialized (host={settings.langfuse_host})")
    except Exception as e:
        logger.warning(f"Langfuse init failed, tracing disabled: {e}")
        return None

    return _langfuse


def flush_langfuse() -> None:
    """Flush pending Langfuse events on shutdown."""
    global _langfuse
    if _langfuse is not None:
        try:
            _langfuse.flush()
        except Exception:
            pass
        _langfuse = None
