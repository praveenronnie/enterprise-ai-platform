# AI Gateway — single entry point for all AI operations
from __future__ import annotations

import logging

from backend.app.platform.ai.exceptions import GatewayError
from backend.app.platform.ai.schemas import (
    ChatMessage,
    EmbeddingRequest,
    EmbeddingResponse,
    GenerateRequest,
    GenerateResponse,
)

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class AIGateway:

    def __init__(self, provider, embedding_service) -> None:
        self._provider = provider
        self._embedding_service = embedding_service

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        try:
            messages = [
                {"role": m.role, "content": m.content} for m in request.messages
            ]
            result = await self._provider.chat_completion(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            choice = result["choices"][0]
            return GenerateResponse(
                content=choice["message"]["content"],
                model=result.get("model", self._provider.model),
                usage=result.get("usage", {}),
            )
        except Exception as exc:
            if isinstance(exc, GatewayError):
                raise
            raise GatewayError(f"Generation failed: {exc}") from exc

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        try:
            model_name = request.model or self._embedding_service.model_name
            vectors = self._embedding_service.embed(request.texts)
            return EmbeddingResponse(
                embeddings=vectors.tolist(),
                model=model_name,
                dimensions=vectors.shape[1] if len(vectors) else 0,
            )

        except Exception as exc:
            if isinstance(exc, GatewayError):
                raise
            raise GatewayError(f"Embedding failed: {exc}") from exc

    async def health(self) -> dict:
        provider_ok = await self._provider.health_check()
        return {
            "provider": "ok" if provider_ok else "unreachable",
            "embedding": "ok",
        }
