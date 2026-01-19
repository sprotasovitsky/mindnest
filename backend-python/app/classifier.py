"""Message classifier using LLM.

Classifies user messages and extracts data to save:
- DATA: New information to store in knowledge graph
- QUESTION: Query requiring search and response
- BOTH: Message contains new data AND asks a question
"""

import logging
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from .llm import generate_text
from .prompts import load_prompt

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    DATA = "DATA"
    QUESTION = "QUESTION"
    BOTH = "BOTH"


class ClassificationResult(BaseModel):
    message_type: MessageType
    data_to_save: Optional[str] = None  # Extracted/expanded data for Graphiti
    search_query: Optional[str] = None
    confidence: float = 1.0


async def classify_message(
    message: str,
    user_name: Optional[str] = None,
    chat_history: Optional[str] = None,
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
    prompt = prompt_template.format(
        message=message,
        user_name=user_name or "User",
        chat_history=chat_history or "(no history)",
    )

    try:
        response = await generate_text(prompt)
        result = _parse_classification(response)
        logger.info(
            f"Classified: type={result.message_type} "
            f"data_to_save={'yes' if result.data_to_save else 'no'} "
            f"search_query={'yes' if result.search_query else 'no'}"
        )
        return result
    except Exception as e:
        logger.error(f"Classification failed: {e}")
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
    search_query = None

    for line in lines:
        line = line.strip()
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
        elif line.startswith("SEARCH_QUERY:"):
            query = line.replace("SEARCH_QUERY:", "").strip()
            if query.lower() != "none" and query:
                search_query = query

    return ClassificationResult(
        message_type=message_type,
        data_to_save=data_to_save,
        search_query=search_query,
    )
