"""Graph store service – manages knowledge graph entities and relations.

The base protocol is defined here; all implementation classes should conform
to the same public interface so the rest of the application can remain
provider-agnostic.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from backend.app.shared.models.models import Document, Entity, Graph, Relation

logger = logging.getLogger(__name__)


class GraphStoreBase(ABC):
    """Pluggable graph-store interface.

    Extend this class when adding a new graph-database provider.
    """

    @abstractmethod
    async def sync_document_graph(
        self,
        document: Document,
        new_entities: list[Entity],
        new_relations: list[Relation],
        removed_entity_ids: list[str] | None = None,
        removed_relation_ids: list[str] | None = None,
    ) -> None: ...

    @abstractmethod
    async def get_document_entities(self, document_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_related_entities(
        self, entity_id: str, max_depth: int = 2
    ) -> list[dict[str, Any]]: ...


class InMemoryGraphStore:
    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._relations: dict[str, Relation] = {}
        self._graphs: dict[str, Graph] = {}

    def add_entity(self, entity: Entity) -> None:
        self._entities[entity.entity_id] = entity

    def add_entities(self, entities: list[Entity]) -> None:
        for entity in entities:
            self.add_entity(entity)

    def add_relation(self, relation: Relation) -> None:
        self._relations[relation.relation_id] = relation

    def add_relations(self, relations: list[Relation]) -> None:
        for relation in relations:
            self.add_relation(relation)

    def build_graph(
        self, document: Document, entities: list[Entity], relations: list[Relation]
    ) -> Graph:
        graph = Graph(
            graph_id=f"{document.document_id}-graph",
            document_id=document.document_id,
            entity_ids=[e.entity_id for e in entities],
            relationship_ids=[r.relation_id for r in relations],
        )
        self._graphs[graph.graph_id] = graph
        logger.info(
            "Built graph %s with %d entities and %d relations.",
            graph.graph_id,
            len(entities),
            len(relations),
        )
        return graph

    def upsert_entity(self, entity: Entity) -> None:
        self._entities[entity.entity_id] = entity
        logger.debug("Upserted entity: %s", entity.entity_id)

    def upsert_relation(self, relation: Relation) -> None:
        self._relations[relation.relation_id] = relation
        logger.debug("Upserted relation: %s", relation.relation_id)

    def remove_entities(self, entity_ids: list[str]) -> None:
        for eid in entity_ids:
            self._entities.pop(eid, None)
        if entity_ids:
            logger.info("Removed %d entities.", len(entity_ids))

    def remove_relations(self, relation_ids: list[str]) -> None:
        for rid in relation_ids:
            self._relations.pop(rid, None)
        if relation_ids:
            logger.info("Removed %d relations.", len(relation_ids))

    def get_entity(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def get_relation(self, relation_id: str) -> Relation | None:
        return self._relations.get(relation_id)

    def get_graph(self, graph_id: str) -> Graph | None:
        return self._graphs.get(graph_id)

    def get_document_graph(self, document_id: str) -> Graph | None:
        graph_id = f"{document_id}-graph"
        return self._graphs.get(graph_id)

    def get_document_entities(self, document_id: str) -> list[Entity]:
        return [e for e in self._entities.values() if e.document_id == document_id]

    def get_document_relations(self, document_id: str) -> list[Relation]:
        return [r for r in self._relations.values() if r.document_id == document_id]

    def sync_document_graph(
        self,
        document: Document,
        new_entities: list[Entity],
        new_relations: list[Relation],
        removed_entity_ids: list[str] | None = None,
        removed_relation_ids: list[str] | None = None,
    ) -> Graph:
        if removed_entity_ids:
            self.remove_entities(removed_entity_ids)
        if removed_relation_ids:
            self.remove_relations(removed_relation_ids)
        for entity in new_entities:
            self.upsert_entity(entity)
        for relation in new_relations:
            self.upsert_relation(relation)
        all_entities = self.get_document_entities(document.document_id)
        all_relations = self.get_document_relations(document.document_id)
        graph = self.build_graph(document, all_entities, all_relations)
        return graph

    def get_related_entities(
        self, entity_id: str, max_depth: int = 2
    ) -> list[dict[str, Any]]:
        visited: set[str] = set()
        results: list[dict[str, Any]] = []
        queue: list[tuple[str, int, str]] = [(entity_id, 0, "self")]
        while queue:
            current_id, depth, relation_type = queue.pop(0)
            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)
            entity = self._entities.get(current_id)
            if entity:
                results.append(
                    {
                        "entity": entity,
                        "depth": depth,
                        "relation": relation_type,
                    }
                )
            if depth < max_depth:
                for rel in self._relations.values():
                    if rel.source_entity_id == current_id:
                        queue.append((rel.target_entity_id, depth + 1, rel.relation))
                    elif rel.target_entity_id == current_id:
                        queue.append((rel.source_entity_id, depth + 1, rel.relation))
        return results

    def clear(self) -> None:
        self._entities.clear()
        self._relations.clear()
        self._graphs.clear()
