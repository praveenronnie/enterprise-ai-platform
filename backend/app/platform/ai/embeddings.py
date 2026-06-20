# Embedding service — generates embeddings using Sentence Transformers
from __future__ import annotations

import logging
from typing import ClassVar

from sentence_transformers import SentenceTransformer

from backend.app.platform.ai.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingService:

    _model: ClassVar[SentenceTransformer | None] = None

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    def _load_model(self) -> SentenceTransformer:
        if EmbeddingService._model is None:
            try:
                EmbeddingService._model = SentenceTransformer(self._model_name)
            except Exception as exc:
                raise EmbeddingError(
                    f"Failed to load embedding model '{self._model_name}': {exc}"
                ) from exc
        return EmbeddingService._model

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            raise EmbeddingError("Cannot embed empty text list")
        model = self._load_model()
        try:
            embeddings = model.encode(texts, convert_to_numpy=False)
            return [list(vec) for vec in embeddings]
        except Exception as exc:
            raise EmbeddingError(f"Embedding generation failed: {exc}") from exc

    def embed_dimensions(self) -> int:
        model = self._load_model()
        return model.get_embedding_dimension()
