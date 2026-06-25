"""Resume extraction logic using Pydantic models."""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from backend.app.plugins.base import DocumentPlugin
from backend.app.plugins.resume.models import ResumeExtraction
from backend.app.shared.models.models import Document, Entity, Relation
from backend.app.platform.ai.gateway import AIGateway
from backend.app.platform.ai.schemas import ChatMessage, GenerateRequest

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = (
    "You are a resume parsing assistant. Extract structured information "
    "from the following resume text. Return only valid JSON matching the schema."
)


class ResumePlugin(DocumentPlugin):
    display_name = "Resume Parser"
    plugin_type = "resume"
    graph_worthy = True
    preferred_provider = None
    output_model = ResumeExtraction

    def __init__(self, ai_gateway: AIGateway | None = None) -> None:
        self._gateway = ai_gateway

    async def extract(self, raw_text: str, document: Document) -> dict[str, Any]:
        if not self._gateway:
            logger.warning("No AI gateway provided - returning empty extraction.")
            return {}

        schema_json = ResumeExtraction.model_json_schema()
        prompt = self._build_extraction_prompt(raw_text, schema_json)
        request = GenerateRequest(
            messages=[ChatMessage(role="system", content=prompt)],
            temperature=0.1,
            max_tokens=2000,
        )
        response = await self._gateway.generate(request)
        return self._parse_extraction_response(response)

    def _build_extraction_prompt(self, raw_text: str, schema_json: dict) -> str:
        return (
            f"{EXTRACTION_PROMPT}\n\n"
            f"--- Resume Text ---\n{raw_text}\n\n"
            f"--- Schema ---\n{json.dumps(schema_json, indent=2)}"
        )

    def _parse_extraction_response(self, response: Any) -> dict[str, Any]:
        try:
            data = json.loads(response.content)
            validated = ResumeExtraction.model_validate(data)
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("Failed to parse/validate extraction output: %s", exc)
            return {"raw_output": response.content}

    async def extract_entities_and_relations(
        self, extracted: dict[str, Any], document: Document
    ) -> tuple[list[Entity], list[Relation]]:
        entities: list[Entity] = []
        relations: list[Relation] = []

        person_entity = self._create_person_entity(extracted, document)
        if person_entity:
            entities.append(person_entity)

        for skill in extracted.get("skills", []):
            skill_entity = self._create_skill_entity(skill, document)
            entities.append(skill_entity)
            if person_entity:
                relations.append(
                    Relation(
                        relation_id=f"{document.document_id}-has-skill-{len(relations)}",
                        document_id=document.document_id,
                        source_entity_id=person_entity.entity_id,
                        target_entity_id=skill_entity.entity_id,
                        relation="has_skill",
                    )
                )

        for exp in extracted.get("experience", []):
            if not (company := exp.get("company")):
                continue

            company_entity = Entity(
                entity_id=f"{document.document_id}-company-{self._normalize_entity_id(company)}",
                document_id=document.document_id,
                chunk_id="",
                name=company,
                label="Organization",
            )
            entities.append(company_entity)
            if person_entity:
                relations.append(
                    Relation(
                        relation_id=f"{document.document_id}-worked-at-{len(relations)}",
                        document_id=document.document_id,
                        source_entity_id=person_entity.entity_id,
                        target_entity_id=company_entity.entity_id,
                        relation="worked_at",
                        properties={
                            "role": exp.get("role", ""),
                            "duration": exp.get("duration", ""),
                        },
                    )
                )

        return entities, relations

    def _normalize_entity_id(self, name: str) -> str:
        """Normalize a name for use in entity IDs."""
        return name.lower().replace(" ", "_")

    def _create_person_entity(
        self, extracted: dict[str, Any], document: Document
    ) -> Entity | None:
        """Create a Person entity from extracted resume data."""
        if not (name := extracted.get("candidate_name")):
            return None

        return Entity(
            entity_id=f"{document.document_id}-person",
            document_id=document.document_id,
            chunk_id="",
            name=name,
            label="Person",
            properties={
                "email": extracted.get("email", ""),
                "phone": extracted.get("phone", ""),
            },
        )

    def _create_skill_entity(self, skill: str, document: Document) -> Entity:
        """Create a Skill entity for a single skill."""
        return Entity(
            entity_id=f"{document.document_id}-skill-{self._normalize_entity_id(skill)}",
            document_id=document.document_id,
            chunk_id="",
            name=skill,
            label="Skill",
        )
