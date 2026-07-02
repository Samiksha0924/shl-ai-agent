from typing import List, Optional

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """
    Structured representation of the user's hiring requirements.
    """

    role: Optional[str] = None

    purpose: Optional[str] = None

    experience_level: Optional[str] = None

    skills: List[str] = Field(default_factory=list)

    assessment_types: List[str] = Field(default_factory=list)

    job_levels: List[str] = Field(default_factory=list)

    max_duration: Optional[int] = None

    language: Optional[str] = None

    remote_testing: Optional[bool] = None

    adaptive_testing: Optional[bool] = None

    additional_constraints: List[str] = Field(default_factory=list)

    confidence: float = 1.0

    # NEW
    role_confirmed: bool = False
    completed: bool = False