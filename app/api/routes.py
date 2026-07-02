from fastapi import APIRouter

from app.api.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
)
from app.api.chat_schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
)

from app.models.context import ConversationContext
from app.services.conversation_engine import ConversationEngine
from app.services.hybrid_retriever import HybridRetriever
from app.services.chat_orchestrator import ChatOrchestrator
from app.llm.groq_client import GroqClient

router = APIRouter()

# =========================
# LAZY INITIALIZATION (FIX)
# =========================

engine = None
retriever = None
chat_orchestrator = None


def get_engine():
    global engine
    if engine is None:
        engine = ConversationEngine()
    return engine


def get_retriever():
    global retriever
    if retriever is None:
        retriever = HybridRetriever()
    return retriever


def get_chat_orchestrator():
    global chat_orchestrator
    if chat_orchestrator is None:
        chat_orchestrator = ChatOrchestrator(
            engine=get_engine(),
            retriever=get_retriever(),
        )
    return chat_orchestrator


def get_groq_client():
    # optional safe init (for test endpoint)
    return GroqClient()


# =========================
# HEALTH CHECK
# =========================
@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


# =========================
# CHAT ENDPOINT (spec-required)
# =========================
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    orchestrator = get_chat_orchestrator()

    result = orchestrator.handle(request.messages)

    return ChatResponse(**result)


# =========================
# LEGACY ENDPOINT (kept for your own testing)
# =========================
@router.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest):

    # IMPORTANT: use lazy init here
    engine = get_engine()
    retriever = get_retriever()

    context = ConversationContext()

    result = engine.process(
        request.query,
        context,
    )

    if result["needs_clarification"]:
        return RecommendationResponse(
            success=False,
            message=result["question"],
            recommendations=[],
        )

    requirement = result["requirement"]

    recommendations = retriever.retrieve(
        query=request.query,
        requirement=requirement,
    )

    items = []

    for assessment in recommendations:
        items.append(
            RecommendationItem(
                name=assessment.name,
                url=str(assessment.url),
                duration=assessment.duration,
                remote=assessment.remote,
                adaptive=assessment.adaptive,
                similarity_score=round(
                    getattr(assessment, "similarity_score", 0.0), 3
                ),
            )
        )

    return RecommendationResponse(
        success=True,
        message="Recommendations generated successfully.",
        recommendations=items,
    )


# =========================
# DEBUG ENDPOINT (GROQ TEST)
# =========================
@router.get("/test-groq")
def test_groq():

    client = get_groq_client()

    response = client.chat(
        system_prompt="Return only valid JSON with field status",
        user_prompt="Say if you are working",
    )

    return {"raw_response": response}