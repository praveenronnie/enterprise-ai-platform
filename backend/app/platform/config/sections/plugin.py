# plugin configuration
from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.platform.config.sections.common import JsonList


class PluginSettings(BaseModel):

    PLUGIN_ENABLED: bool = Field(
        description="Master switch to enable/disable the plugin system.",
    )
    PLUGIN_DIRECTORIES: str = Field(
        description="Colon-separated list of directories to scan for plugins.",
    )
    PLUGIN_ALLOWED: JsonList = Field(
        description="List of explicitly allowed plugin names (empty = allow all).",
    )
    PLUGIN_BLOCKED: JsonList = Field(
        description="List of explicitly blocked plugin names.",
    )
