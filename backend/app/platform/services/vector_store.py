"""Vector store service – manages document embeddings and similarity search.

The base protocol is defined here; all implementation classes should conform
to the same public interface so the rest of the application can remain
provider-agnostic.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from backend.app.platform.ai.gateway import AIGateway
from backend.app.platform.ai.schemas import EmbeddingRequest
from backend.app.shared.models.models import Chunk

logger = logging.getLogger(__name__)


class VectorStoreBase(ABC):
    """Pluggable vector-store interface.

    Low-level methods that operate on raw embeddings.
    Extend this class when adding a new vector-database provider.
    """

    @abstractmethod
    async def upsert_chunks(
        self, entries: list[VectorStoreEntry]
    ) -> None: ...

    @abstractmethod
    async def search(
        self, embedding: list[float], top_k: int = 5, document_id: str | None = None
    ) -> list[VectorStoreEntry]: ...

    @abstractmethod
    async def remove_chunks(self, chunk_ids: list[str]) -> None: ...

    @abstractmethod
    async def count(self) -> int: ...


class VectorStoreEntry:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        text: str,
        embedding: list[float],
        content_hash: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.text = text
        self.embedding = embedding
        self.content_hash = content_hash
        self.metadata = metadata or {}


class VectorStore:
    def __init__(self, ai_gateway: AIGateway) -> None:
        self._gateway = ai_gateway
        self._entries: list[VectorStoreEntry] = []

    async def add_chunk(self, chunk: Chunk, document_id: str) -> None:
        response = await self._gateway.embed(EmbeddingRequest(texts=[chunk.text]))
        if not response.embeddings:
            logger.warning("Empty embedding for chunk %s.", chunk.chunk_id)
            return
        entry = VectorStoreEntry(
            chunk_id=chunk.chunk_id,
            document_id=document_id,
            text=chunk.text,
            embedding=response.embeddings[0],
            content_hash=chunk.content_hash,
            metadata={
                "section_title": chunk.section_title,
                "page_numbers": chunk.page_numbers,
            },
        )
        self._entries.append(entry)
        logger.debug("Added chunk %s to vector store.", chunk.chunk_id)

    async def add_chunks(self, chunks: list[Chunk], document_id: str) -> None:
        for chunk in chunks:
            await self.add_chunk(chunk, document_id)

    async def upsert_chunk(self, chunk: Chunk, document_id: str) -> None:
        existing = [e for e in self._entries if e.chunk_id == chunk.chunk_id]
        if existing:
            self._entries = [e for e in self._entries if e.chunk_id != chunk.chunk_id]
            logger.debug("Removed existing entry for chunk %s for re-upsert.", chunk.chunk_id)
        await self.add_chunk(chunk, document_id)

    async def remove_chunks(self, chunk_ids: list[str]) -> None:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.chunk_id not in chunk_ids]
        removed = before - len(self._entries)
        if removed:
            logger.info("Removed %d chunks from vector store.", removed)

    def get_chunk_ids_for_document(self, document_id: str) -> list[str]:
        return [e.chunk_id for e in self._entries if e.document_id == document_id]

    def has_content_hash(self, document_id: str, content_hash: str) -> bool:
        for e in self._entries:
            if e.document_id == document_id and e.content_hash == content_hash:
                return True
        return False

    async def search(self, query: str, top_k: int = 5) -> list[VectorStoreEntry]:
        if not self._entries:
            return []
        response = await self._gateway.embed(EmbeddingRequest(texts=[query]))
        if not response.embeddings:
            return []
        query_embedding = response.embeddings[0]
        scored: list[tuple[float, VectorStoreEntry]] = []
        for entry in self._entries:
            score = self._cosine_similarity(query_embedding, entry.embedding)
            scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for score, entry in scored[:top_k] if score > 0.0]

    async def search_by_document(
        self, query: str, document_id: str, top_k: int = 5
    ) -> list[VectorStoreEntry]:
        all_results = await self.search(query, top_k=top_k * 2)
        return [r for r in all_results if r.document_id == document_id][:top_k]

    def clear(self) -> None:
        self._entries.clear()

    def count(self) -> int:
        return len(self._entries)

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)