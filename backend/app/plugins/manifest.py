"""Plugin manifest loader - reads/writes the manifest JSON file."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.json"


class PluginManifestEntry:
    """A single entry in the plugin manifest."""

    def __init__(
        self,
        plugin_type: str,
        display_name: str,
        module: str,
        schema: dict[str, Any],
        extraction_prompt: str,
        graph_worthy: bool = False,
        preferred_provider: str | None = None,
        enabled: bool = True,
        output_model: str | None = None,
        class_path: str | None = None,
    ) -> None:
        self.plugin_type = plugin_type
        self.display_name = display_name
        self.module = module
        self.schema = schema
        self.extraction_prompt = extraction_prompt
        self.graph_worthy = graph_worthy
        self.preferred_provider = preferred_provider
        self.enabled = enabled
        self.output_model = output_model
        self.class_path = class_path

    def to_dict(self) -> dict[str, Any]:
        data = {
            "plugin_type": self.plugin_type,
            "display_name": self.display_name,
            "module": self.module,
            "schema": self.schema,
            "extraction_prompt": self.extraction_prompt,
            "graph_worthy": self.graph_worthy,
            "preferred_provider": self.preferred_provider,
            "enabled": self.enabled,
        }
        if self.output_model:
            data["output_model"] = self.output_model
        if self.class_path:
            data["class"] = self.class_path
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginManifestEntry:
        return cls(
            plugin_type=data["plugin_type"],
            display_name=data.get("display_name", data["plugin_type"]),
            module=data["module"],
            schema=data.get("schema", {}),
            extraction_prompt=data.get("extraction_prompt", ""),
            graph_worthy=data.get("graph_worthy", False),
            preferred_provider=data.get("preferred_provider"),
            enabled=data.get("enabled", True),
            output_model=data.get("output_model"),
            class_path=data.get("class"),
        )


class ManifestManager:
    """Reads and writes the plugin manifest JSON file."""

    def __init__(self, manifest_path: Path = MANIFEST_PATH) -> None:
        self._path = manifest_path

    def load(self) -> list[PluginManifestEntry]:
        if not self._path.exists():
            logger.warning(
                "Manifest file not found at %s - returning empty list.", self._path
            )
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            entries = raw if isinstance(raw, list) else raw.get("plugins", [])
            return [PluginManifestEntry.from_dict(e) for e in entries]
        except Exception:
            logger.exception("Failed to load plugin manifest.")
            return []

    def save(self, entries: list[PluginManifestEntry]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(
                {"plugins": [e.to_dict() for e in entries]},
                f,
                indent=2,
                ensure_ascii=False,
            )
        logger.info("Manifest saved to %s (%d plugins).", self._path, len(entries))

    def add_entry(self, entry: PluginManifestEntry) -> list[PluginManifestEntry]:
        entries = self.load()
        entries = [e for e in entries if e.plugin_type != entry.plugin_type]
        entries.append(entry)
        self.save(entries)
        return entries

    def remove_entry(self, plugin_type: str) -> list[PluginManifestEntry]:
        entries = self.load()
        entries = [e for e in entries if e.plugin_type != plugin_type]
        self.save(entries)
        return entries

    def get_entry(self, plugin_type: str) -> PluginManifestEntry | None:
        entries = self.load()
        for e in entries:
            if e.plugin_type == plugin_type:
                return e
        return None
