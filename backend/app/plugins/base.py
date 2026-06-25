"""Base protocol and registry for document plugins."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from backend.app.shared.models.models import Document, Entity, Relation

logger = logging.getLogger(__name__)


class DocumentPlugin(ABC):
    """Interface every document-type plugin must implement."""

    display_name: str
    plugin_type: str
    schema: dict[str, Any]
    extraction_prompt: str
    graph_worthy: bool
    preferred_provider: str | None = None
    output_model: type[BaseModel] | None = None

    @abstractmethod
    async def extract(self, raw_text: str, document: Document) -> dict[str, Any]: ...

    @abstractmethod
    async def extract_entities_and_relations(
        self, extracted: dict[str, Any], document: Document
    ) -> tuple[list[Entity], list[Relation]]: ...

    def post_process(self, document: Document, extracted: dict[str, Any]) -> Document:
        return document


class PluginRegistry:
    """Thread-safe registry that loads plugins from a manifest and makes them
    available to the ingestion pipeline."""

    def __init__(self) -> None:
        self._plugins: dict[str, DocumentPlugin] = {}

    def register(self, plugin: DocumentPlugin) -> None:
        if plugin.plugin_type in self._plugins:
            logger.warning(
                "Overwriting existing plugin '%s' with a new instance.",
                plugin.plugin_type,
            )
        self._plugins[plugin.plugin_type] = plugin
        logger.info(
            "Registered plugin '%s' (type=%s, graph_worthy=%s).",
            plugin.display_name,
            plugin.plugin_type,
            plugin.graph_worthy,
        )

    def unregister(self, plugin_type: str) -> None:
        removed = self._plugins.pop(plugin_type, None)
        if removed:
            logger.info("Unregistered plugin type '%s'.", plugin_type)
        else:
            logger.warning("Plugin type '%s' not found.", plugin_type)

    def get(self, plugin_type: str) -> DocumentPlugin | None:
        return self._plugins.get(plugin_type)

    def list_types(self) -> list[str]:
        return list(self._plugins)

    def list_all(self) -> list[DocumentPlugin]:
        return list(self._plugins.values())

    def has_type(self, plugin_type: str) -> bool:
        return plugin_type in self._plugins

    def __len__(self) -> int:
        return len(self._plugins)


registry: PluginRegistry = PluginRegistry()
