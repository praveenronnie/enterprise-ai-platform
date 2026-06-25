"""Tests for the plugin framework."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.plugins.base import DocumentPlugin, PluginRegistry, registry
from backend.app.plugins.manifest import ManifestManager, PluginManifestEntry
from backend.app.shared.models.models import Document, Entity, Relation


# ── Mock Plugin ────────────────────────────────────────────────────────────


class MockPlugin(DocumentPlugin):
    display_name = "Mock Parser"
    plugin_type = "mock"
    graph_worthy = True
    preferred_provider = None
    schema = {"type": "object", "properties": {"test_field": {"type": "string"}}}
    extraction_prompt = "Extract test data."

    async def extract(self, raw_text: str, document: Document) -> dict:  # type: ignore[override]
        return {"test_field": "mock_value"}

    async def extract_entities_and_relations(
        self, extracted: dict, document: Document
    ) -> tuple[list[Entity], list[Relation]]:
        entity = Entity(
            entity_id=f"{document.document_id}-test",
            document_id=document.document_id,
            chunk_id="",
            name="TestEntity",
            label="Test",
        )
        return [entity], []


# ── Tests ──────────────────────────────────────────────────────────────────


class TestPluginRegistry:
    def test_register_and_get(self) -> None:
        reg = PluginRegistry()
        plugin = MockPlugin()
        reg.register(plugin)
        assert reg.get("mock") is plugin
        assert reg.has_type("mock") is True

    def test_unregister(self) -> None:
        reg = PluginRegistry()
        reg.register(MockPlugin())
        reg.unregister("mock")
        assert reg.get("mock") is None

    def test_list_types(self) -> None:
        reg = PluginRegistry()
        reg.register(MockPlugin())
        assert "mock" in reg.list_types()

    def test_list_all(self) -> None:
        reg = PluginRegistry()
        reg.register(MockPlugin())
        assert len(reg.list_all()) == 1


class TestPluginManifestEntry:
    def test_to_dict_and_from_dict(self) -> None:
        entry = PluginManifestEntry(
            plugin_type="test",
            display_name="Test Plugin",
            module="test_module",
            schema={"type": "object"},
            extraction_prompt="test prompt",
            graph_worthy=True,
        )
        data = entry.to_dict()
        restored = PluginManifestEntry.from_dict(data)
        assert restored.plugin_type == "test"
        assert restored.graph_worthy is True
        assert restored.schema == {"type": "object"}


class TestManifestManager:
    def test_save_and_load(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "manifest.json"
        manager = ManifestManager(manifest_path)

        entry = PluginManifestEntry(
            plugin_type="resume",
            display_name="Resume Parser",
            module="resume",
            schema={},
            extraction_prompt="test",
            graph_worthy=True,
        )
        manager.add_entry(entry)
        loaded = manager.load()
        assert len(loaded) == 1
        assert loaded[0].plugin_type == "resume"

    def test_remove_entry(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "manifest.json"
        manager = ManifestManager(manifest_path)

        entry = PluginManifestEntry(
            plugin_type="resume",
            display_name="Resume Parser",
            module="resume",
            schema={},
            extraction_prompt="test",
            graph_worthy=True,
        )
        manager.add_entry(entry)
        manager.remove_entry("resume")
        assert len(manager.load()) == 0


class TestPluginExtraction:
    @pytest.mark.asyncio
    async def test_mock_extraction(self) -> None:
        plugin = MockPlugin()
        doc = Document(
            document_id="test-123",
            filename="test.pdf",
            file_type="application/pdf",
            file_size=100,
            checksum="abc",
            binary_hash="def",
        )
        extracted = await plugin.extract("dummy text", doc)
        assert extracted["test_field"] == "mock_value"

    @pytest.mark.asyncio
    async def test_mock_entity_extraction(self) -> None:
        plugin = MockPlugin()
        doc = Document(
            document_id="test-123",
            filename="test.pdf",
            file_type="application/pdf",
            file_size=100,
            checksum="abc",
            binary_hash="def",
        )
        entities, relations = await plugin.extract_entities_and_relations(
            {"test_field": "value"}, doc
        )
        assert len(entities) == 1
        assert entities[0].label == "Test"


if __name__ == "__main__":
    pytest.main([__file__])