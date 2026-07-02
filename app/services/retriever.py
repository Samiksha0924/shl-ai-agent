from typing import List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.models.assessment import Assessment
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


class Retriever:

    def __init__(self):
        self.embedding_service = None
        self.vector_store = None

        self.index = None
        self.assessments = []
        self.embeddings = None

    # -------------------------
    # LAZY LOADING (IMPORTANT FIX)
    # -------------------------
    def _load(self):
        if self.embedding_service is None:
            self.embedding_service = EmbeddingService()

        if self.vector_store is None:
            self.vector_store = VectorStore()
            self.index, self.assessments = self.vector_store.load()
            self.embeddings = self.vector_store.embeddings

        if self.index is None:
            raise RuntimeError("FAISS index not loaded properly")

    # -------------------------
    # MAIN SEARCH
    # -------------------------
    def search(self, query: str, top_k: int = 5) -> List[Assessment]:

        self._load()

        try:
            query_embedding = self.embedding_service.embed_query(query)

            scores, indices = self.index.search(
                np.array(query_embedding).reshape(1, -1),
                top_k,
            )

            results = []

            for score, idx in zip(scores[0], indices[0]):

                if idx == -1:
                    continue

                if idx >= len(self.assessments):
                    continue

                assessment = self.assessments[idx]

                assessment.__dict__["similarity_score"] = float(score)
                results.append(assessment)

            return results

        except Exception as e:
            print("Retriever search error:", str(e))
            return []

    # -------------------------
    # SAFE FALLBACK SEARCH
    # -------------------------
    def search_from_candidates(
        self,
        query: str,
        candidates: List[Assessment],
        top_k: int = 5,
    ) -> List[Assessment]:

        self._load()

        if not candidates:
            return []

        try:
            query_embedding = self.embedding_service.embed_query(query)

            candidate_embeddings = []
            candidate_objects = []

            for assessment in candidates:

                try:
                    idx = self.assessments.index(assessment)
                    candidate_embeddings.append(self.embeddings[idx])
                    candidate_objects.append(assessment)
                except Exception:
                    continue

            if not candidate_embeddings:
                return []

            similarities = cosine_similarity(
                query_embedding,
                np.array(candidate_embeddings),
            )[0]

            ranked = sorted(
                zip(similarities, candidate_objects),
                key=lambda x: x[0],
                reverse=True,
            )

            results = []

            for score, assessment in ranked[:top_k]:
                assessment.__dict__["similarity_score"] = float(score)
                results.append(assessment)

            return results

        except Exception as e:
            print("Candidate search error:", str(e))
            return []