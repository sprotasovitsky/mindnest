"""Message classifier using LLM.

Classifies user messages and extracts data to save:
- DATA: New information to store in knowledge graph
- QUESTION: Query requiring search and response
- BOTH: Message contains new data AND asks a question
"""

from enum import Enum
from typing import Optional

import structlog
from pydantic import BaseModel

from .llm import generate_text
from .metrics import message_type_counter
from .prompts import load_prompt

logger = structlog.get_logger(__name__)


class MessageType(str, Enum):
    DATA = "DATA"
    QUESTION = "QUESTION"
    BOTH = "BOTH"


class ClassificationResult(BaseModel):
    message_type: MessageType
    data_to_save: Optional[str] = None  # Extracted/expanded data for Graphiti
    search_queries: list[str] = []  # One or more search queries for multi-query search
    confidence: float = 1.0

    @property
    def search_query(self) -> Optional[str]:
        """Primary search query (first one) for backward compatibility."""
        return self.search_queries[0] if self.search_queries else None


async def classify_message(
    message: str,
    user_name: Optional[str] = None,
    chat_history: Optional[str] = None,
    trace_id: Optional[str] = None,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> ClassificationResult:
    """Classify a user message and extract data using LLM.

    Args:
        message: The user's message to classify
        user_name: Name of the user sending the message
        chat_history: Last 4 messages for context resolution (optional)

    Returns:
        ClassificationResult with type, data_to_save, and search_query
    """
    prompt_template = load_prompt("classifier")
    cot_suffix = (
        "\n\nBefore answering, briefly explain your reasoning:\n"
        "1. What facts/data are present in the message?\n"
        "2. What questions are asked?\n"
        "Then give the final output in the required format."
    )
    prompt = prompt_template.format(
        message=message,
        user_name=user_name or "User",
        chat_history=chat_history or "(no history)",
    ) + cot_suffix

    try:
        response = await generate_text(
            prompt,
            prompt_name="classifier",
            step="classify",
            trace_id=trace_id,
            project_id=project_id,
            user_id=user_id,
        )
        result = _parse_classification(response)

        # Up to 2 retries if BOTH but no data extracted
        if result.message_type == MessageType.BOTH and not result.data_to_save:
            for retry in range(2):
                logger.info(f"BOTH with no data — retry {retry + 1}/2")
                response = await generate_text(
                    prompt,
                    prompt_name="classifier",
                    step=f"classify_retry_{retry + 1}",
                    trace_id=trace_id,
                    project_id=project_id,
                    user_id=user_id,
                )
                result = _parse_classification(response)
                if result.data_to_save:
                    break

            # Final fallback: use original message as data
            if result.message_type == MessageType.BOTH and not result.data_to_save:
                logger.warning("BOTH with no data after 2 retries — using original message")
                result.data_to_save = message

        message_type_counter.labels(message_type=result.message_type.value).inc()

        logger.info(
            "classified",
            message_type=result.message_type,
            has_data=bool(result.data_to_save),
            search_queries=len(result.search_queries),
            trace_id=trace_id,
        )
        return result
    except Exception as e:
        logger.error("classification_failed", error=str(e), trace_id=trace_id)
        # Default to DATA to avoid losing information
        return ClassificationResult(
            message_type=MessageType.DATA,
            data_to_save=message,  # Save original message as fallback
            confidence=0.5,
        )


def _parse_classification(response: str) -> ClassificationResult:
    """Parse LLM response into ClassificationResult."""
    lines = response.strip().split("\n")

    message_type = MessageType.DATA
    data_to_save = None
    search_queries: list[str] = []

    for line in lines:
        line = line.strip().replace("*", "").strip()
        if line.startswith("TYPE:"):
            type_str = line.replace("TYPE:", "").strip().upper()
            if type_str == "QUESTION":
                message_type = MessageType.QUESTION
            elif type_str == "BOTH":
                message_type = MessageType.BOTH
            else:
                message_type = MessageType.DATA
        elif line.startswith("DATA_TO_SAVE:"):
            data = line.replace("DATA_TO_SAVE:", "").strip()
            if data.lower() != "none" and data:
                data_to_save = data
        elif line.startswith("SEARCH_QUERIES:") or line.startswith("SEARCH_QUERY:"):
            raw = line.split(":", 1)[1].strip()
            if raw.lower() != "none" and raw:
                # Split by " | " for multi-query, fall back to single query
                queries = [q.strip() for q in raw.split("|") if q.strip()]
                search_queries = queries[:3]  # Cap at 3 queries

    return ClassificationResult(
        message_type=message_type,
        data_to_save=data_to_save,
        search_queries=search_queries,
    )
