"""Plugin management API – CRUD endpoints for document type plugins."""

from __future__ import annotations

import importlib
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.plugins.base import registry
from backend.app.plugins.manifest import ManifestManager, PluginManifestEntry

logger = logging.getLogger(__name__)

router = APIRouter()
manifest_manager = ManifestManager()


# ── Request / Response Models ──────────────────────────────────────────────


class PluginCreateRequest(BaseModel):
    plugin_type: str = Field(..., description="Unique plugin type identifier.")
    display_name: str = Field(..., description="Human-readable name.")
    module: str = Field(..., description="Python module name (without .py).")
    extraction_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for extraction."
    )
    extraction_prompt: str = Field(
        "", description="LLM prompt template for extraction."
    )
    graph_worthy: bool = Field(False, description="Whether to build a knowledge graph.")
    preferred_provider: str | None = Field(None, description="Preferred LLM provider.")
    enabled: bool = Field(True, description="Whether the plugin is active.")

    model_config = {"populate_by_name": True}


class PluginUpdateRequest(BaseModel):
    display_name: str | None = None
    extraction_schema: dict[str, Any] | None = None
    extraction_prompt: str | None = None
    graph_worthy: bool | None = None
    preferred_provider: str | None = None
    enabled: bool | None = None

    model_config = {"populate_by_name": True}


class PluginResponse(BaseModel):
    plugin_type: str
    display_name: str
    module: str
    graph_worthy: bool
    enabled: bool
    preferred_provider: str | None
    schema_fields: list[str]
    output_model: str | None = None


class PluginListResponse(BaseModel):
    plugins: list[PluginResponse]
    total: int


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.get("/plugins", response_model=PluginListResponse)
async def list_plugins() -> PluginListResponse:
    """List all registered plugins."""
    all_plugins = registry.list_all()
    plugins_response = []
    for p in all_plugins:
        schema_fields = []
        output_model_name = None
        if hasattr(p, "output_model") and p.output_model:
            try:
                schema = p.output_model.model_json_schema()
                schema_fields = list(schema.get("properties", {}).keys())
                output_model_name = f"{p.output_model.__module__}.{p.output_model.__name__}"
            except Exception:
                schema_fields = list(getattr(p, "schema", {}).get("properties", {}).keys())
        else:
            schema_fields = list(getattr(p, "schema", {}).get("properties", {}).keys())

        plugins_response.append(
            PluginResponse(
                plugin_type=p.plugin_type,
                display_name=p.display_name,
                module=type(p).__module__,
                graph_worthy=p.graph_worthy,
                enabled=True,
                preferred_provider=p.preferred_provider,
                schema_fields=schema_fields,
                output_model=output_model_name,
            )
        )
    return PluginListResponse(plugins=plugins_response, total=len(plugins_response))


@router.post(
    "/plugins", response_model=PluginResponse, status_code=status.HTTP_201_CREATED
)
async def add_plugin(request: PluginCreateRequest) -> PluginResponse:
    """Register a new plugin from the manifest.
    The plugin module must already exist and contain a class that matches
    the naming convention: <ModuleName>Plugin (e.g., resume -> ResumePlugin).
    """
    try:
        module = importlib.import_module(f"backend.app.plugins.{request.module}")
        class_name = f"{request.module.capitalize()}Plugin"
        plugin_class = getattr(module, class_name, None)
        if plugin_class is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plugin class '{class_name}' not found in module '{request.module}'.",
            )
        plugin = plugin_class()
        registry.register(plugin)
        entry = PluginManifestEntry(
            plugin_type=request.plugin_type,
            display_name=request.display_name,
            module=request.module,
            schema=request.extraction_schema,
            extraction_prompt=request.extraction_prompt,
            graph_worthy=request.graph_worthy,
            preferred_provider=request.preferred_provider,
            enabled=request.enabled,
        )
        manifest_manager.add_entry(entry)
        logger.info("Plugin '%s' added successfully.", request.plugin_type)
        return PluginResponse(
            plugin_type=plugin.plugin_type,
            display_name=plugin.display_name,
            module=type(plugin).__module__,
            graph_worthy=plugin.graph_worthy,
            enabled=request.enabled,
            preferred_provider=plugin.preferred_provider,
            schema_fields=list(
                getattr(plugin, "schema", {}).get("properties", {}).keys()
            ),
        )
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to import module '{request.module}': {exc}",
        ) from exc


@router.delete("/plugins/{plugin_type}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plugin(plugin_type: str) -> None:
    """Remove a plugin by type."""
    registry.unregister(plugin_type)
    manifest_manager.remove_entry(plugin_type)
    logger.info("Plugin '%s' removed.", plugin_type)


@router.get("/plugins/{plugin_type}", response_model=PluginResponse)
async def get_plugin(plugin_type: str) -> PluginResponse:
    """Get details for a specific plugin."""
    plugin = registry.get(plugin_type)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_type}' not found.",
        )
    entry = manifest_manager.get_entry(plugin_type)
    schema_fields = []
    output_model_name = None
    if hasattr(plugin, "output_model") and plugin.output_model:
        try:
            schema = plugin.output_model.model_json_schema()
            schema_fields = list(schema.get("properties", {}).keys())
            output_model_name = f"{plugin.output_model.__module__}.{plugin.output_model.__name__}"
        except Exception:
            schema_fields = list(getattr(plugin, "schema", {}).get("properties", {}).keys())
    else:
        schema_fields = list(getattr(plugin, "schema", {}).get("properties", {}).keys())

    return PluginResponse(
        plugin_type=plugin.plugin_type,
        display_name=plugin.display_name,
        module=type(plugin).__module__,
        graph_worthy=plugin.graph_worthy,
        enabled=entry.enabled if entry else True,
        preferred_provider=plugin.preferred_provider,
        schema_fields=schema_fields,
        output_model=output_model_name,
    )


@router.put("/plugins/{plugin_type}", response_model=PluginResponse)
async def update_plugin(
    plugin_type: str, request: PluginUpdateRequest
) -> PluginResponse:
    """Update plugin metadata in the manifest."""
    entry = manifest_manager.get_entry(plugin_type)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_type}' not found in manifest.",
        )
    if request.display_name is not None:
        entry.display_name = request.display_name
    if request.extraction_schema is not None:
        entry.schema = request.extraction_schema
    if request.extraction_prompt is not None:
        entry.extraction_prompt = request.extraction_prompt
    if request.graph_worthy is not None:
        entry.graph_worthy = request.graph_worthy
    if request.preferred_provider is not None:
        entry.preferred_provider = request.preferred_provider
    if request.enabled is not None:
        entry.enabled = request.enabled
    manifest_manager.add_entry(entry)
    plugin = registry.get(plugin_type)
    if plugin:
        schema_fields = []
        output_model_name = None
        if hasattr(plugin, "output_model") and plugin.output_model:
            try:
                schema = plugin.output_model.model_json_schema()
                schema_fields = list(schema.get("properties", {}).keys())
                output_model_name = f"{plugin.output_model.__module__}.{plugin.output_model.__name__}"
            except Exception:
                schema_fields = list(getattr(plugin, "schema", {}).get("properties", {}).keys())
        else:
            schema_fields = list(getattr(plugin, "schema", {}).get("properties", {}).keys())

        return PluginResponse(
            plugin_type=plugin.plugin_type,
            display_name=plugin.display_name,
            module=type(plugin).__module__,
            graph_worthy=plugin.graph_worthy,
            enabled=entry.enabled,
            preferred_provider=plugin.preferred_provider,
            schema_fields=schema_fields,
            output_model=output_model_name,
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Plugin '{plugin_type}' not found in registry.",
    )
