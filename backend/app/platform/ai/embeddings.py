# Embedding service — generates embeddings using Sentence Transformers
from __future__ import annotations

import logging
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.platform.ai.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

        logger.info("Loading embedding model: %s", model_name)
        try:
            self._model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as exc:
            logger.exception("Failed to load embedding model")
            raise EmbeddingError(
                f"Failed to load embedding model '{model_name}': {exc}"
            ) from exc

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            raise EmbeddingError("Cannot embed empty text list")

        try:
            embeddings = self._model.encode(texts, convert_to_numpy=False)
            return np.asarray(embeddings)
        except Exception as exc:
            raise EmbeddingError(f"Embedding generation failed: {exc}") from exc

    def embed_dimensions(self) -> int:
        return self._model.get_embedding_dimension()
