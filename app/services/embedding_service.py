from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:
    """
    Generates vector embeddings for assessment documents.
    Uses lazy loading to prevent startup crashes.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self.model = None  # ❌ don't load at startup

    def _load_model(self):
        """Load model only when required"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)

    def embed_documents(self, documents: list[str]) -> np.ndarray:
        self._load_model()

        return self.model.encode(
            documents,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

    def embed_query(self, query: str) -> np.ndarray:
        self._load_model()

        embedding = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embedding.reshape(1, -1)