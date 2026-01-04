"""Chat API Router.

Handles chat messages and response generation.
This replaces the Java ChatController and AgentService.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import google.generativeai as genai

from ..config import get_settings
from ..graphiti_client import get_knowledge_graph, KnowledgeGraph

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


# Request/Response models
class ChatRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., min_length=1, max_length=10000)
    project_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    user_name: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response."""
    reply: str
    sources: list[str] = []
    confidence: float = 1.0
    entities_extracted: int = 0


class SearchRequest(BaseModel):
    """Search request."""
    query: str = Field(..., min_length=1)
    project_id: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)


class SearchResponse(BaseModel):
    """Search response."""
    facts: list[dict]
    entities: list[dict]


# Initialize Gemini
settings = get_settings()
if settings.google_api_key:
    genai.configure(api_key=settings.google_api_key)


async def generate_response(
    message: str,
    context: dict,
    user_name: Optional[str] = None,
) -> str:
    """Generate a response using Gemini with knowledge graph context.

    Args:
        message: User's message
        context: Context from knowledge graph (facts, entities)
        user_name: Optional user name for personalization

    Returns:
        Generated response text
    """
    model = genai.GenerativeModel(settings.llm_model)

    user_context = f"User {user_name} says" if user_name else "User says"

    prompt = f"""You are a helpful AI assistant managing knowledge and tasks for a team.
You have access to the following context from the knowledge base:

{context['context_text']}

{user_context}: {message}

Instructions:
- Answer based on the context when relevant
- If creating/updating tasks or facts, confirm what was saved
- Be concise and helpful
- If you don't have enough context, say so
- Respond in the same language as the user's message

Response:"""

    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        return "Sorry, I encountered an error generating a response. Please try again."


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
) -> ChatResponse:
    """Process a chat message.

    This endpoint:
    1. Adds the message to the knowledge graph (Graphiti extracts entities/edges)
    2. Retrieves relevant context from the graph
    3. Generates a response using the LLM

    The knowledge graph automatically handles:
    - Entity extraction (people, tasks, expenses, etc.)
    - Edge creation and normalization
    - Temporal invalidation (updates/deletions)
    """
    logger.info(f"Processing message for project {request.project_id}: {request.message[:50]}...")

    # Step 1: Add message to knowledge graph
    # Graphiti will extract entities and create edges
    add_result = await kg.add_message(
        message=request.message,
        project_id=request.project_id,
        user_id=request.user_id,
        user_name=request.user_name,
    )

    if not add_result["success"]:
        logger.warning(f"Failed to add message to graph: {add_result.get('error')}")

    # Step 2: Get context from knowledge graph
    context = await kg.get_context_for_response(
        query=request.message,
        project_id=request.project_id,
    )

    # Step 3: Generate response
    reply = await generate_response(
        message=request.message,
        context=context,
        user_name=request.user_name,
    )

    # Extract source facts for response
    sources = [f["fact"] for f in context["facts"][:5]]

    return ChatResponse(
        reply=reply,
        sources=sources,
        confidence=1.0 if context["facts"] else 0.7,
        entities_extracted=add_result.get("nodes_created", 0),
    )


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
) -> SearchResponse:
    """Search the knowledge graph.

    Uses Graphiti's hybrid search:
    - Semantic similarity
    - BM25 keyword matching
    - Graph traversal
    """
    logger.info(f"Searching in project {request.project_id}: {request.query[:50]}...")

    result = await kg.search(
        query=request.query,
        project_id=request.project_id,
        limit=request.limit,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Search failed"))

    return SearchResponse(
        facts=result["facts"],
        entities=result["entities"],
    )


@router.get("/health")
async def health_check(
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
) -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "graphiti_initialized": kg._initialized,
        "timestamp": datetime.now().isoformat(),
    }
