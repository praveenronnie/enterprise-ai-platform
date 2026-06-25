"""Document type detection service."""

from __future__ import annotations

import json
import logging
from typing import Any

from backend.app.platform.ai.gateway import AIGateway
from backend.app.platform.ai.schemas import ChatMessage, GenerateRequest
from backend.app.platform.ai.prompts.common import DETECTION_PROMPT
from backend.app.plugins.base import registry
from backend.app.plugins.manifest import ManifestManager

logger = logging.getLogger(__name__)


class DocumentTypeDetector:
    def __init__(
        self, ai_gateway: AIGateway, manifest_manager: ManifestManager | None = None
    ) -> None:
        self._gateway = ai_gateway
        self._manifest = manifest_manager or ManifestManager()

    async def detect(self, raw_text: str) -> str:
        types = registry.list_types()
        if not types:
            logger.warning("No plugins registered - cannot detect document type.")
            return "unknown"

        prompt = DETECTION_PROMPT.format(type_list="\n".join(f"  - {t}" for t in types))
        text_sample = raw_text[:2000]

        request = GenerateRequest(
            messages=[
                ChatMessage(role="system", content=prompt),
                ChatMessage(
                    role="user", content=f"--- Document text ---\n{text_sample}"
                ),
            ],
            temperature=0.0,
            max_tokens=100,
        )
        response = await self._gateway.generate(request)

        try:
            result = json.loads(response.content.strip())
            doc_type = result.get("document_type", "unknown")
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse detection output: %s", response.content)
            doc_type = "unknown"

        if doc_type not in types:
            logger.info(
                "Detected type '%s' is not registered - falling back to 'unknown'.",
                doc_type,
            )
            doc_type = "unknown"

        return doc_type
