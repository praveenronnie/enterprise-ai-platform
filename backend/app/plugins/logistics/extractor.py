"""Logistics extraction logic using Pydantic models."""

from __future__ import annotations

import json
import logging
from typing import Any

from backend.app.plugins.base import DocumentPlugin
from backend.app.plugins.logistics.models import LogisticsExtraction
from backend.app.shared.models.models import Document, Entity, Relation
from backend.app.platform.ai.gateway import AIGateway
from backend.app.platform.ai.schemas import ChatMessage, GenerateRequest

LogisticsExtractionModel = LogisticsExtraction

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = (
    "You are a logistics document parsing assistant. Extract structured "
    "shipment information from the following document text. Return only valid JSON matching the schema."
)


class LogisticsPlugin(DocumentPlugin):
    display_name = "Logistics Document Parser"
    plugin_type = "logistics"
    graph_worthy = True
    preferred_provider = None
    output_model = LogisticsExtractionModel

    def __init__(self, ai_gateway: AIGateway | None = None) -> None:
        self._gateway = ai_gateway

    async def extract(self, raw_text: str, document: Document) -> dict[str, Any]:
        if not self._gateway:
            logger.warning("No AI gateway provided - returning empty extraction.")
            return {}

        schema_json = LogisticsExtraction.model_json_schema()
        prompt = (
            f"{EXTRACTION_PROMPT}\n\n"
            f"--- Document Text ---\n{raw_text}\n\n"
            f"--- Schema ---\n{json.dumps(schema_json, indent=2)}"
        )
        request = GenerateRequest(
            messages=[ChatMessage(role="system", content=prompt)],
            temperature=0.1,
            max_tokens=2000,
        )
        response = await self._gateway.generate(request)
        try:
            data = json.loads(response.content)
            validated = LogisticsExtraction.model_validate(data)
            return validated.model_dump()
        except (json.JSONDecodeError, Exception) as exc:
            logger.error("Failed to parse/validate extraction output: %s", exc)
            return {"raw_output": response.content}

    async def extract_entities_and_relations(
        self, extracted: dict[str, Any], document: Document
    ) -> tuple[list[Entity], list[Relation]]:
        entities: list[Entity] = []
        relations: list[Relation] = []

        if shipment_id := extracted.get("shipment_id"):
            entities.append(
                Entity(
                    entity_id=f"{document.document_id}-shipment",
                    document_id=document.document_id,
                    chunk_id="",
                    name=shipment_id,
                    label="Shipment",
                    properties={
                        "status": extracted.get("status", ""),
                        "carrier": extracted.get("carrier", ""),
                    },
                )
            )

        if origin := extracted.get("origin"):
            origin_entity = Entity(
                entity_id=f"{document.document_id}-origin",
                document_id=document.document_id,
                chunk_id="",
                name=origin,
                label="Location",
            )
            entities.append(origin_entity)
            if len(entities) >= 2:
                relations.append(
                    Relation(
                        relation_id=f"{document.document_id}-origin-of",
                        document_id=document.document_id,
                        source_entity_id=entities[0].entity_id,
                        target_entity_id=origin_entity.entity_id,
                        relation="originates_from",
                    )
                )

        if destination := extracted.get("destination"):
            dest_entity = Entity(
                entity_id=f"{document.document_id}-destination",
                document_id=document.document_id,
                chunk_id="",
                name=destination,
                label="Location",
            )
            entities.append(dest_entity)
            if entities:
                relations.append(
                    Relation(
                        relation_id=f"{document.document_id}-destination-of",
                        document_id=document.document_id,
                        source_entity_id=entities[0].entity_id,
                        target_entity_id=dest_entity.entity_id,
                        relation="delivers_to",
                    )
                )

        if carrier := extracted.get("carrier"):
            carrier_entity = Entity(
                entity_id=f"{document.document_id}-carrier",
                document_id=document.document_id,
                chunk_id="",
                name=carrier,
                label="Organization",
            )
            entities.append(carrier_entity)
            if entities:
                relations.append(
                    Relation(
                        relation_id=f"{document.document_id}-carried-by",
                        document_id=document.document_id,
                        source_entity_id=entities[0].entity_id,
                        target_entity_id=carrier_entity.entity_id,
                        relation="carried_by",
                    )
                )

        return entities, relations