"""Chat API Router.

Handles chat messages and response generation.
This replaces the Java ChatController and AgentService.
"""

import logging
from datetime import datetime
from typing import Optional

import os
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from google import genai

from ..config import get_settings
from ..graphiti_client import get_knowledge_graph, KnowledgeGraph
from .auth import get_user_from_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get current user from Authorization header (optional)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return get_user_from_token(token)


# Request/Response models
class ChatRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., min_length=1, max_length=10000)
    # Support both formats: projectId (old Java) and project_id (new)
    projectId: Optional[str] = Field(None, min_length=1)
    project_id: Optional[str] = Field(None, min_length=1)
    user_id: Optional[str] = None
    user_name: Optional[str] = None

    def get_project_id(self) -> str:
        """Get project ID from either field."""
        return self.projectId or self.project_id or ""


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


# Initialize Gemini client
settings = get_settings()
_genai_client = None

def get_genai_client():
    """Get or create Gemini client."""
    global _genai_client
    if _genai_client is None:
        api_key = settings.google_api_key
        if api_key:
            _genai_client = genai.Client(api_key=api_key)
        else:
            # Use Vertex AI with ADC
            if settings.google_application_credentials:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
            _genai_client = genai.Client(
                vertexai=True,
                project=settings.vertex_ai_project_id,
                location=settings.vertex_ai_location,
            )
    return _genai_client


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
    client = get_genai_client()

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
        response = await client.aio.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        return "Sorry, I encountered an error generating a response. Please try again."


async def process_chat_message(
    request: ChatRequest,
    kg: KnowledgeGraph,
    user: Optional[dict] = None,
) -> ChatResponse:
    """Process a chat message (internal function).

    This function:
    1. Adds the message to the knowledge graph (Graphiti extracts entities/edges)
    2. Retrieves relevant context from the graph
    3. Generates a response using the LLM

    The knowledge graph automatically handles:
    - Entity extraction (people, tasks, expenses, etc.)
    - Edge creation and normalization
    - Temporal invalidation (updates/deletions)
    """
    project_id = request.get_project_id()
    user_id = request.user_id or (user["id"] if user else "anonymous")
    user_name = request.user_name or (user["name"] if user else None)

    logger.info(f"Processing message for project {project_id}: {request.message[:50]}...")

    # Step 1: Add message to knowledge graph
    # Graphiti will extract entities and create edges
    add_result = await kg.add_message(
        message=request.message,
        project_id=project_id,
        user_id=user_id,
        user_name=user_name,
    )

    if not add_result["success"]:
        logger.warning(f"Failed to add message to graph: {add_result.get('error')}")

    # Step 2: Get context from knowledge graph
    context = await kg.get_context_for_response(
        query=request.message,
        project_id=project_id,
    )

    # Step 3: Generate response
    reply = await generate_response(
        message=request.message,
        context=context,
        user_name=user_name,
    )

    # Extract source facts for response
    sources = [f["fact"] for f in context["facts"][:5]]

    return ChatResponse(
        reply=reply,
        sources=sources,
        confidence=1.0 if context["facts"] else 0.7,
        entities_extracted=add_result.get("nodes_created", 0),
    )


# Main chat endpoint (compatible with old Java API: POST /api/chat)
@router.post("/api/chat", response_model=ChatResponse)
async def send_message_legacy(
    request: ChatRequest,
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
    user: Optional[dict] = Depends(get_current_user_optional),
) -> ChatResponse:
    """Process a chat message (legacy endpoint for compatibility)."""
    return await process_chat_message(request, kg, user)


# New endpoint path
@router.post("/api/chat/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
    user: Optional[dict] = Depends(get_current_user_optional),
) -> ChatResponse:
    """Process a chat message."""
    return await process_chat_message(request, kg, user)


@router.post("/api/chat/search", response_model=SearchResponse)
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


@router.get("/api/chat/health")
async def health_check(
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
) -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "graphiti_initialized": kg._initialized,
        "timestamp": datetime.now().isoformat(),
    }
