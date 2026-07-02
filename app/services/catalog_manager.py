from typing import Dict, List, Optional

from app.models.assessment import Assessment
from app.services.catalog_loader import CatalogLoader


class CatalogManager:
    """
    In-memory catalog manager.

    Loads the SHL catalog once and provides
    helper methods for retrieval.
    """

    def __init__(self):

        self.loader = CatalogLoader()

        self.assessments: List[Assessment] = self.loader.load()

        self.lookup: Dict[str, Assessment] = {
            assessment.entity_id: assessment
            for assessment in self.assessments
        }

    def get_all(self) -> List[Assessment]:
        return self.assessments

    def get_by_id(self, entity_id: str) -> Optional[Assessment]:
        return self.lookup.get(entity_id)

    def total_assessments(self) -> int:
        return len(self.assessments)

    def get_embedding_documents(self) -> List[str]:
        return [
            assessment.embedding_text
            for assessment in self.assessments
            if assessment.embedding_text
        ]