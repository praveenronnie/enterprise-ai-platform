"""Neo4j graph store – persists entities and relations to a Neo4j database."""

from __future__ import annotations

import logging
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from backend.app.platform.config.loader import EnvironmentLoader
from backend.app.platform.services.graph_store import GraphStoreBase
from backend.app.shared.models.models import Document, Entity, Relation

logger = logging.getLogger(__name__)


class Neo4jGraphStore(GraphStoreBase):
    """Thin wrapper around the Neo4j async driver.

    Reads connection parameters from EnvironmentLoader.
    """

    def __init__(self, env: dict[str, Any] | None = None) -> None:
        if env is None:
            env = EnvironmentLoader().load()

        uri: str = env.get("LOCAL_GRAPH_URL", "bolt://localhost:7687")
        user: str = env.get("LOCAL_GRAPH_USERNAME", "graphdb")
        password: str = env.get("LOCAL_GRAPH_PASSWORD", "graphdb123")

        self._driver: AsyncDriver = AsyncGraphDatabase.driver(
            uri, auth=(user, password)
        )

    async def verify_connectivity(self) -> bool:
        """Check that the database is reachable."""
        try:
            await self._driver.verify_connectivity()
            return True
        except Exception as exc:
            logger.warning("Neo4j connectivity check failed: %s", exc)
            return False

    async def create_document_node(self, document: Document) -> None:
        """Create or update a Document node."""
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (d:Document {document_id: $document_id})
                SET d.filename = $filename,
                    d.file_type = $file_type,
                    d.file_size = $file_size,
                    d.title = $title,
                    d.summary = $summary,
                    d.language = $language,
                    d.total_pages = $total_pages,
                    d.total_words = $total_words,
                    d.updated_at = timestamp()
                """,
                document_id=document.document_id,
                filename=document.filename,
                file_type=document.file_type,
                file_size=document.file_size,
                title=document.title,
                summary=document.summary,
                language=document.language,
                total_pages=document.total_pages,
                total_words=document.total_words,
            )
        logger.debug("Upserted Document node %s.", document.document_id)

    async def upsert_entity(self, entity: Entity) -> None:
        """Create or update an Entity node."""
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (e:Entity {entity_id: $entity_id})
                SET e.name = $name,
                    e.label = $label,
                    e.description = $description,
                    e.document_id = $document_id,
                    e.chunk_id = $chunk_id,
                    e.confidence = $confidence
                """,
                entity_id=entity.entity_id,
                name=entity.name,
                label=entity.label,
                description=entity.description,
                document_id=entity.document_id,
                chunk_id=entity.chunk_id,
                confidence=entity.confidence,
            )
        logger.debug("Upserted Entity node %s.", entity.entity_id)

    async def upsert_relation(self, relation: Relation) -> None:
        """Create or update a RELATES_TO relationship between two entities."""
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (source:Entity {entity_id: $source_id})
                MATCH (target:Entity {entity_id: $target_id})
                MERGE (source)-[r:RELATES_TO {relation_id: $relation_id}]->(target)
                SET r.relation = $relation,
                    r.description = $description,
                    r.document_id = $document_id,
                    r.confidence = $confidence
                """,
                source_id=relation.source_entity_id,
                target_id=relation.target_entity_id,
                relation_id=relation.relation_id,
                relation=relation.relation,
                description=relation.description,
                document_id=relation.document_id,
                confidence=relation.confidence,
            )
        logger.debug("Upserted Relation %s.", relation.relation_id)

    async def remove_entities(self, entity_ids: list[str]) -> None:
        """Delete entity nodes and their relationships."""
        if not entity_ids:
            return
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (e:Entity)
                WHERE e.entity_id IN $entity_ids
                DETACH DELETE e
                """,
                entity_ids=entity_ids,
            )
        logger.info("Removed %d entity nodes from Neo4j.", len(entity_ids))

    async def remove_relations(self, relation_ids: list[str]) -> None:
        """Delete relationship edges by their IDs."""
        if not relation_ids:
            return
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH ()-[r:RELATES_TO]->()
                WHERE r.relation_id IN $relation_ids
                DELETE r
                """,
                relation_ids=relation_ids,
            )
        logger.info("Removed %d relations from Neo4j.", len(relation_ids))

    async def sync_document_graph(
        self,
        document: Document,
        new_entities: list[Entity],
        new_relations: list[Relation],
        removed_entity_ids: list[str] | None = None,
        removed_relation_ids: list[str] | None = None,
    ) -> None:
        """Full sync: upsert document node, then upsert/remove entities and relations."""
        await self.create_document_node(document)

        if removed_entity_ids:
            await self.remove_entities(removed_entity_ids)
        if removed_relation_ids:
            await self.remove_relations(removed_relation_ids)

        for entity in new_entities:
            await self.upsert_entity(entity)
        for relation in new_relations:
            await self.upsert_relation(relation)

        logger.info(
            "Graph synced for document %s: %d entities, %d relations.",
            document.document_id,
            len(new_entities),
            len(new_relations),
        )

    async def get_document_entities(self, document_id: str) -> list[dict[str, Any]]:
        """Return all Entity nodes that belong to a given document."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (e:Entity {document_id: $document_id})
                RETURN e.entity_id AS entity_id,
                       e.name AS name,
                       e.label AS label,
                       e.description AS description
                """,
                document_id=document_id,
            )
            records = await result.fetch()
            return [
                {
                    "entity_id": r["entity_id"],
                    "name": r["name"],
                    "label": r["label"],
                    "description": r["description"],
                }
                for r in records
            ]

    async def get_related_entities(
        self, entity_id: str, max_depth: int = 2
    ) -> list[dict[str, Any]]:
        """Traverse the graph from an entity up to *max_depth* hops."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH path = (start:Entity {entity_id: $entity_id})-[:RELATES_TO*1..$max_depth]-(related:Entity)
                UNWIND nodes(path) AS n
                WITH DISTINCT n
                RETURN n.entity_id AS entity_id,
                       n.name AS name,
                       n.label AS label,
                       n.description AS description
                """,
                entity_id=entity_id,
                max_depth=max_depth,
            )
            records = await result.fetch()
            return [
                {
                    "entity_id": r["entity_id"],
                    "name": r["name"],
                    "label": r["label"],
                    "description": r["description"],
                }
                for r in records
            ]

    async def close(self) -> None:
        await self._driver.close()
