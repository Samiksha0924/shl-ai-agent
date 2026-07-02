from typing import List

import numpy as np

from app.models.assessment import Assessment
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


class Retriever:
    """
    Retrieves the most relevant assessments using semantic similarity.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

        self.index, self.assessments = self.vector_store.load()

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Assessment]:

        query_embedding = self.embedding_service.embed_query(query)

        scores, indices = self.index.search(
            query_embedding,
            top_k,
        )

        results = []

        for score, idx in zip(scores[0], indices[0]):

            if idx == -1:
                continue

            assessment = self.assessments[idx]

            # Store similarity score dynamically
            assessment.__dict__["similarity_score"] = float(score)

            results.append(assessment)

        return results