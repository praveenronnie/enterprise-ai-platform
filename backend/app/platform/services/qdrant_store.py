"""Qdrant vector store – persists embeddings to a Qdrant collection."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from backend.app.platform.config.loader import EnvironmentLoader
from backend.app.platform.services.vector_store import VectorStoreBase, VectorStoreEntry

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStoreBase):
    """Thin wrapper around the Qdrant async client.

    Reads connection parameters from EnvironmentLoader so it works
    with the existing settings system.
    """

    def __init__(self, env: dict[str, Any] | None = None) -> None:
        if env is None:
            env = EnvironmentLoader().load()

        self._url: str = env.get("VECTOR_DB_URL", "http://localhost:6333")
        self._collection: str = env.get(
            "VECTOR_DB_INDEX_NAME", "enterprise-document-engine"
        )
        self._dimension: int = int(env.get("VECTOR_DB_DIMENSION", 1024))
        self._metric: str = env.get("VECTOR_DB_METRIC", "cosine")

        self._client: AsyncQdrantClient = AsyncQdrantClient(url=self._url)

    async def ensure_collection(self) -> None:
        """Create the collection if it does not exist yet."""
        collections = await self._client.get_collections()
        existing = {c.name for c in collections.collections}
        if self._collection not in existing:
            distance = Distance.COSINE if self._metric == "cosine" else Distance.EUCLID
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(
                    size=self._dimension,
                    distance=distance,
                ),
            )
            logger.info(
                "Created Qdrant collection '%s' (dim=%d).",
                self._collection,
                self._dimension,
            )

    def _generate_point_id(self, chunk_id: str) -> str:
        """Generate a valid UUID for Qdrant from a chunk ID string."""
        # Use UUID5 with a fixed namespace to generate deterministic UUIDs
        namespace = uuid.NAMESPACE_DNS
        return str(uuid.uuid5(namespace, chunk_id))

    async def upsert(
        self,
        chunk_id: str,
        document_id: str,
        embedding: list[float],
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Upsert a single point."""
        point_id = self._generate_point_id(chunk_id)
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "document_id": document_id,
                "chunk_id": chunk_id,
                **(payload or {}),
            },
        )
        await self._client.upsert(
            collection_name=self._collection,
            points=[point],
        )
        logger.debug("Upserted point %s (chunk: %s) to Qdrant.", point_id, chunk_id)

    async def upsert_chunks(
        self,
        entries: list[VectorStoreEntry],
    ) -> None:
        """Batch-upsert multiple entries."""
        points: list[PointStruct] = []
        for entry in entries:
            point_id = self._generate_point_id(entry.chunk_id)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=entry.embedding,
                    payload={
                        "document_id": entry.document_id,
                        "chunk_id": entry.chunk_id,
                        "text": entry.text,
                        "content_hash": entry.content_hash,
                        "section_title": entry.metadata.get("section_title"),
                        "page_numbers": entry.metadata.get("page_numbers"),
                    },
                )
            )
        if points:
            await self._client.upsert(
                collection_name=self._collection,
                points=points,
            )
            logger.debug("Upserted %d points to Qdrant.", len(points))

    async def search(
        self,
        embedding: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[VectorStoreEntry]:
        """Search for nearest neighbours."""
        filter_ = None
        if document_id:
            from qdrant_client.models import FieldCondition, MatchValue

            filter_ = FieldCondition(
                key="document_id",
                match=MatchValue(value=document_id),
            )

        results = await self._client.search(
            collection_name=self._collection,
            query_vector=embedding,
            limit=top_k,
            query_filter=filter_,
        )

        entries: list[VectorStoreEntry] = []
        for scored in results:
            payload = scored.payload or {}
            # Retrieve the original chunk_id from payload, fallback to point ID
            chunk_id = payload.get("chunk_id", str(scored.id))
            entries.append(
                VectorStoreEntry(
                    chunk_id=chunk_id,
                    document_id=payload.get("document_id", ""),
                    text=payload.get("text", ""),
                    embedding=scored.vector or [],
                    content_hash=payload.get("content_hash", ""),
                    metadata={
                        "section_title": payload.get("section_title"),
                        "page_numbers": payload.get("page_numbers"),
                    },
                )
            )
        return entries

    async def remove_chunks(self, chunk_ids: list[str]) -> None:
        """Delete points by their chunk IDs."""
        if chunk_ids:
            # Convert chunk IDs to Qdrant point IDs
            point_ids = [self._generate_point_id(chunk_id) for chunk_id in chunk_ids]
            await self._client.delete(
                collection_name=self._collection,
                points_selector=point_ids,
            )
            logger.info("Removed %d points from Qdrant.", len(chunk_ids))

    async def count(self) -> int:
        """Return the total number of points in the collection."""
        result = await self._client.count(collection_name=self._collection)
        return result.count or 0

    async def close(self) -> None:
        await self._client.close()
