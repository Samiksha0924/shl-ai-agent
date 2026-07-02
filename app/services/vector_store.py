import pickle

import faiss
import numpy as np

from app.core.constants import VECTOR_STORE_PATH
from app.services.catalog_manager import CatalogManager
from app.services.embedding_service import EmbeddingService


class VectorStore:
    """
    Handles building, saving and loading the FAISS index
    together with assessment metadata and embeddings.
    """

    def __init__(self):

        self.catalog = CatalogManager()
        self.embedding_service = EmbeddingService()

        VECTOR_STORE_PATH.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.index_path = VECTOR_STORE_PATH / "shl.index"

        self.mapping_path = VECTOR_STORE_PATH / "mapping.pkl"

        self.embedding_path = VECTOR_STORE_PATH / "embeddings.npy"

        self.embeddings = None

    def build(self):

        assessments = self.catalog.get_all()

        documents = [
            assessment.embedding_text
            for assessment in assessments
        ]

        embeddings = self.embedding_service.embed_documents(
            documents
        )

        self.embeddings = embeddings

        dimension = embeddings.shape[1]

        index = faiss.IndexFlatIP(dimension)

        index.add(embeddings)

        faiss.write_index(
            index,
            str(self.index_path),
        )

        with open(self.mapping_path, "wb") as f:
            pickle.dump(
                assessments,
                f,
            )

        np.save(
            self.embedding_path,
            embeddings,
        )

        print(f"Indexed {len(assessments)} assessments.")

    def load(self):

        index = faiss.read_index(
            str(self.index_path)
        )

        with open(self.mapping_path, "rb") as f:

            assessments = pickle.load(f)

        self.embeddings = np.load(
            self.embedding_path
        )

        return index, assessments