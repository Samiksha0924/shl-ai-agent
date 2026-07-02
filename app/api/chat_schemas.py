from typing import List, Literal, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatRecommendationItem(BaseModel):
    name: str
    url: str
    test_type: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    # FIX: spec/sample traces show `recommendations: null` for turns that
    # are clarifying, refusing, or comparing — not `[]`. List[...] = []
    # could never serialize as null, which is a schema mismatch against
    # the documented trace format. Only the turn that actually commits to
    # a shortlist should populate this with 1-10 items.
    recommendations: Optional[List[ChatRecommendationItem]] = None
    end_of_conversation: bool = False


class HealthResponse(BaseModel):
    status: str