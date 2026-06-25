"""In-memory document repository keyed by binary_hash for duplicate detection."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.shared.models.models import Chunk, Document, Entity, Relation

logger = logging.getLogger(__name__)


class DocumentRepository:
    """In-memory repository for document lookup by binary_hash.

    In production this would be backed by a database or cache (Redis, Postgres, etc.).
    """

    def __init__(self) -> None:
        self._by_hash: dict[str, Document] = {}
        self._chunks_by_doc: dict[str, list[Chunk]] = {}
        self._entities_by_doc: dict[str, list[Entity]] = {}
        self._relations_by_doc: dict[str, list[Relation]] = {}

    def find_by_binary_hash(self, binary_hash: str) -> Document | None:
        return self._by_hash.get(binary_hash)

    def store(self, document: Document) -> None:
        self._by_hash[document.binary_hash] = document
        self._chunks_by_doc[document.document_id] = list(document.chunks)
        logger.info("Stored document %s (hash=%s)", document.document_id, document.binary_hash[:12])

    def remove(self, document_id: str) -> None:
        doc = self._by_hash.pop(document_id, None)
        self._chunks_by_doc.pop(document_id, None)
        self._entities_by_doc.pop(document_id, None)
        self._relations_by_doc.pop(document_id, None)
        if doc:
            logger.info("Removed document %s from repository.", document_id)

    def get_chunks(self, document_id: str) -> list[Chunk]:
        return self._chunks_by_doc.get(document_id, [])

    def set_chunks(self, document_id: str, chunks: list[Chunk]) -> None:
        self._chunks_by_doc[document_id] = chunks

    def get_entities(self, document_id: str) -> list[Entity]:
        return self._entities_by_doc.get(document_id, [])

    def set_entities(self, document_id: str, entities: list[Entity]) -> None:
        self._entities_by_doc[document_id] = entities

    def get_relations(self, document_id: str) -> list[Relation]:
        return self._relations_by_doc.get(document_id, [])

    def set_relations(self, document_id: str, relations: list[Relation]) -> None:
        self._relations_by_doc[document_id] = relations

    def has_hash(self, binary_hash: str) -> bool:
        return binary_hash in self._by_hash

    def clear(self) -> None:
        self._by_hash.clear()
        self._chunks_by_doc.clear()
        self._entities_by_doc.clear()
        self._relations_by_doc.clear()


doc_repository: DocumentRepository = DocumentRepository()