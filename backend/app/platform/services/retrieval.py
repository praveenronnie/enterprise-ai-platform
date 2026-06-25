"""Retrieval service - combines vector search with graph context."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.platform.services.graph_store import GraphStoreBase
from backend.app.platform.services.vector_store import VectorStore, VectorStoreEntry

logger = logging.getLogger(__name__)


class RetrievalResult:
    def __init__(
        self,
        chunk: VectorStoreEntry,
        score: float,
        graph_context: list[dict[str, Any]] | None = None,
    ) -> None:
        self.chunk = chunk
        self.score = score
        self.graph_context = graph_context or []


class RetrievalService:
    def __init__(
        self,
        vector_store: VectorStore,
        graph_store: GraphStoreBase,
    ) -> None:
        self._vector_store = vector_store
        self._graph_store = graph_store

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        include_graph: bool = True,
        document_id: str | None = None,
    ) -> list[RetrievalResult]:
        if document_id:
            entries = await self._vector_store.search_by_document(
                query, document_id, top_k=top_k
            )
        else:
            entries = await self._vector_store.search(query, top_k=top_k)

        results: list[RetrievalResult] = []
        for entry in entries:
            graph_context = None
            if include_graph:
                graph_context = await self._get_graph_context(entry.document_id)
            results.append(
                RetrievalResult(chunk=entry, score=0.0, graph_context=graph_context)
            )

        return results

    async def _get_graph_context(self, document_id: str) -> list[dict[str, Any]]:
        """Retrieve graph context for a document from Neo4j."""
        entities = await self._graph_store.get_document_entities(document_id)
        return [
            {
                "entity_id": e["entity_id"],
                "name": e["name"],
                "label": e["label"],
            }
            for e in entities
        ]

    async def retrieve_with_reranking(
        self,
        query: str,
        top_k: int = 10,
        rerank_top: int = 5,
        include_graph: bool = True,
    ) -> list[RetrievalResult]:
        results = await self.retrieve(query, top_k=top_k, include_graph=include_graph)
        return results[:rerank_top]
