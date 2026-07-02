from typing import List

from pydantic import BaseModel

from app.models.assessment import Assessment


class RecommendationResponse(BaseModel):

    state: str

    message: str

    assessments: List[Assessment]

    needs_clarification: bool

    clarification_question: str | None = None