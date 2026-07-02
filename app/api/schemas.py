from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    query: str


class RecommendationItem(BaseModel):
    name: str
    url: str
    duration: int | None = None
    remote: bool
    adaptive: bool
    similarity_score: float


class RecommendationResponse(BaseModel):
    success: bool
    message: str
    recommendations: list[RecommendationItem]