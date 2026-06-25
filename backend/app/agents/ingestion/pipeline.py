"""Incremental ingestion pipeline with PostgreSQL, Qdrant, and Neo4j persistence."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.plugins.base import DocumentPlugin, registry
from backend.app.plugins.manifest import ManifestManager
from backend.app.platform.ai.gateway import AIGateway
from backend.app.platform.ai.schemas import EmbeddingRequest
from backend.app.platform.database import get_db_session
from backend.app.platform.models.document import DocumentRecord
from backend.app.platform.services.document_detector import DocumentTypeDetector
from backend.app.platform.services.graph_store import GraphStoreBase
from backend.app.platform.services.vector_store import (
    VectorStoreBase,
    VectorStore,
    VectorStoreEntry,
)
from backend.app.shared.models.models import Document, Entity, Relation
from backend.app.shared.repositories.document_repository import doc_repository
from backend.app.shared.services.document_processor import (
    process_document,
)
from backend.app.shared.utils.chunk_differ import assign_chunk_hashes, diff_chunks

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        ai_gateway: AIGateway,
        vector_store: VectorStore,
        embedding_store: VectorStoreBase,
        graph_store: GraphStoreBase,
        detector: DocumentTypeDetector,
        manifest_manager: ManifestManager | None = None,
    ) -> None:
        self._gateway = ai_gateway
        self._vector_store = vector_store
        self._embedding_store = embedding_store
        self._graph_store = graph_store
        self._detector = detector
        self._manifest = manifest_manager or ManifestManager()

    async def run(
        self, file_path: str, document: Document, user_id: str | None = None
    ) -> dict[str, Any]:
        logger.info("Starting ingestion for document %s", document.document_id)

        processed_doc = process_document(file_path, document)
        raw_text = processed_doc.extracted_text
        binary_hash = processed_doc.binary_hash

        existing_doc = doc_repository.find_by_binary_hash(binary_hash)
        if existing_doc:
            logger.info("Duplicate document (hash=%s). Skipping.", binary_hash[:12])
            return {
                "document_id": document.document_id,
                "status": "already_indexed",
                "message": "Document with identical binary_hash already exists.",
                "existing_document_id": existing_doc.document_id,
            }

        doc_type = await self._detector.detect(raw_text)
        processed_doc.metadata["detected_type"] = doc_type
        logger.info("Detected document type: %s", doc_type)

        extracted: dict[str, Any] = {}
        entities: list[Entity] = []
        relations: list[Relation] = []
        plugin: DocumentPlugin | None = None

        if doc_type != "unknown":
            plugin = registry.get(doc_type)
            if plugin:
                logger.info("Extracting data via plugin '%s'...", plugin.display_name)
                extracted = await plugin.extract(raw_text, processed_doc)
                processed_doc.metadata["extracted_fields"] = list(extracted.keys())

        if plugin and plugin.graph_worthy and extracted:
            logger.info("Extracting entities and relations...")
            entities, relations = await plugin.extract_entities_and_relations(
                extracted, processed_doc
            )
            processed_doc.entity_ids = [e.entity_id for e in entities]
            processed_doc.relationship_ids = [r.relation_id for r in relations]
            logger.info(
                "Extracted %d entities and %d relations.", len(entities), len(relations)
            )

        old_chunks = doc_repository.get_chunks(processed_doc.document_id)
        new_chunks = processed_doc.chunks
        assign_chunk_hashes(new_chunks)

        # --- Persist chunks and generate embeddings ---
        if old_chunks:
            chunk_diff = diff_chunks(old_chunks, new_chunks)
            logger.info(
                "Chunk diff: %d unchanged, %d updated, %d inserted, %d removed.",
                len(chunk_diff.unchanged),
                len(chunk_diff.updated),
                len(chunk_diff.inserted),
                len(chunk_diff.removed),
            )

            for chunk in chunk_diff.updated:
                await self._vector_store.upsert_chunk(chunk, processed_doc.document_id)

            if chunk_diff.inserted:
                await self._vector_store.add_chunks(
                    chunk_diff.inserted, processed_doc.document_id
                )

            if chunk_diff.removed:
                removed_ids = [c.chunk_id for c in chunk_diff.removed]
                await self._vector_store.remove_chunks(removed_ids)
                await self._embedding_store.remove_chunks(removed_ids)

            # Embed only changed chunks
            chunks_to_embed = chunk_diff.inserted + chunk_diff.updated
            if chunks_to_embed:
                await self._embed_chunks(chunks_to_embed, processed_doc.document_id)
        else:
            logger.info(
                "No previous chunks - persisting and embedding all %d chunks...",
                len(new_chunks),
            )
            await self._vector_store.add_chunks(new_chunks, processed_doc.document_id)
            await self._embed_chunks(new_chunks, processed_doc.document_id)

        processed_doc.embedded = True

        # --- Sync knowledge graph to Neo4j ---
        if entities and relations:
            logger.info("Syncing knowledge graph to Neo4j...")
            old_entities = doc_repository.get_entities(processed_doc.document_id)
            old_relations = doc_repository.get_relations(processed_doc.document_id)

            old_entity_ids = {e.entity_id for e in old_entities}
            new_entity_ids = {e.entity_id for e in entities}
            removed_entity_ids = list(old_entity_ids - new_entity_ids)

            old_rel_keys = {
                (r.source_entity_id, r.target_entity_id, r.relation)
                for r in old_relations
            }
            new_rel_keys = {
                (r.source_entity_id, r.target_entity_id, r.relation) for r in relations
            }
            removed_rel_keys = old_rel_keys - new_rel_keys
            removed_relation_ids = [
                rel.relation_id
                for rel in old_relations
                if (rel.source_entity_id, rel.target_entity_id, rel.relation)
                in removed_rel_keys
            ]

            await self._graph_store.sync_document_graph(
                processed_doc,
                new_entities=entities,
                new_relations=relations,
                removed_entity_ids=removed_entity_ids or None,
                removed_relation_ids=removed_relation_ids or None,
            )
            processed_doc.graph_created = True
            logger.info(
                "Graph synced: %d entities upserted, %d removed; %d relations upserted, %d removed.",
                len(entities),
                len(removed_entity_ids),
                len(relations),
                len(removed_relation_ids),
            )

        # --- Persist document record to PostgreSQL ---
        async for session in get_db_session():
            record = DocumentRecord(
                id=processed_doc.document_id,
                user_id=user_id,
                title=processed_doc.title,
                filename=processed_doc.filename,
                file_type=processed_doc.file_type,
                file_size=processed_doc.file_size,
                source=processed_doc.source,
                checksum=processed_doc.checksum,
                binary_hash=processed_doc.binary_hash,
                doc_version=processed_doc.doc_version,
                status="indexed" if processed_doc.indexed else "processed",
                total_pages=processed_doc.total_pages,
                total_words=processed_doc.total_words,
                summary=processed_doc.summary,
                language=processed_doc.language,
                ocr_status=processed_doc.ocr_status.value,
                ocr_confidence=processed_doc.ocr_confidence,
                metadata_json=(
                    json.dumps(processed_doc.metadata)
                    if processed_doc.metadata
                    else None
                ),
            )
            session.add(record)
            break  # only one session needed

        doc_repository.store(processed_doc)
        doc_repository.set_chunks(processed_doc.document_id, new_chunks)
        doc_repository.set_entities(processed_doc.document_id, entities)
        doc_repository.set_relations(processed_doc.document_id, relations)

        processed_doc.indexed = True

        return {
            "document_id": document.document_id,
            "status": "indexed",
            "doc_type": doc_type,
            "extracted": extracted,
            "entities_count": len(entities),
            "relations_count": len(relations),
        }

    async def _embed_chunks(self, chunks: list[Any], document_id: str) -> None:
        qdrant_entries: list[VectorStoreEntry] = self._vector_store._entries
        if qdrant_entries:
            await self._embedding_store.upsert_chunks(qdrant_entries)
