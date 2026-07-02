from typing import List, Optional

from pydantic import BaseModel, HttpUrl, Field


class Assessment(BaseModel):
    """
    Normalized SHL Assessment object used across the application.
    """

    entity_id: str = Field(..., description="Unique SHL assessment ID")

    name: str

    url: HttpUrl

    description: str

    categories: List[str] = Field(default_factory=list)

    job_levels: List[str] = Field(default_factory=list)

    languages: List[str] = Field(default_factory=list)

    duration: Optional[int] = None

    remote: bool = False

    adaptive: bool = False

    status: str = "unknown"

    # Single-letter SHL test-type code (A/P/K/S/B/C/D), derived from
    # `categories` at load time by CatalogLoader._resolve_test_type().
    # Previously missing entirely — every getattr(assessment, "test_type",
    # None) call across hybrid_retriever.py and chat_orchestrator.py was
    # silently returning None because this field didn't exist on the
    # model, not because of a bug in those call sites.
    test_type: Optional[str] = None

    embedding_text: Optional[str] = None