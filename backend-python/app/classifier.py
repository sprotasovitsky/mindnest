"""Message classifier using LLM.

Classifies user messages into categories to determine processing flow:
- DATA: New information to store in knowledge graph (including corrections/updates)
- QUESTION: Query requiring search and response (questions, calculations, analysis)
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


class ClassificationResult(BaseModel):
    message_type: MessageType
    search_query: Optional[str] = None
    confidence: float = 1.0


async def classify_message(
    message: str,
    user_name: Optional[str] = None,
) -> ClassificationResult:
    """Classify a user message using LLM."""
    prompt_template = load_prompt("classifier")
    prompt = prompt_template.format(
        message=message,
        user_name=user_name or "User",
    )

    try:
        response = await generate_text(prompt)
        return _parse_classification(response)
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return ClassificationResult(message_type=MessageType.DATA, confidence=0.5)


def _parse_classification(response: str) -> ClassificationResult:
    """Parse LLM response into ClassificationResult."""
    lines = response.strip().split("\n")

    message_type = MessageType.DATA
    search_query = None

    for line in lines:
        line = line.strip()
        if line.startswith("TYPE:"):
            type_str = line.replace("TYPE:", "").strip().upper()
            if type_str == "QUESTION":
                message_type = MessageType.QUESTION
            else:
                message_type = MessageType.DATA
        elif line.startswith("SEARCH_QUERY:"):
            query = line.replace("SEARCH_QUERY:", "").strip()
            if query.lower() != "none":
                search_query = query

    return ClassificationResult(
        message_type=message_type,
        search_query=search_query,
    )
