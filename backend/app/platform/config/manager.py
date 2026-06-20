# Configuration manager
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.platform.config.sections import (
    ApiSettings,
    ApplicationSettings,
    DatabaseSettings,
    GraphDatabaseSettings,
    LLMSettings,
    LoggingSettings,
    PluginSettings,
    StorageSettings,
    VectorDatabaseSettings,
)
from backend.app.platform.config.settings import Settings


class ConfigurationManager:

    def __init__(self, raw_config: dict[str, Any]) -> None:
        self._raw: dict[str, Any] = raw_config

    def build(self) -> Settings:
        return Settings(
            application=self._build_application(),
            api=self._build_api(),
            logging=self._build_logging(),
            database=self._build_database(),
            llm=self._build_llm(),
            vector_database=self._build_vector_database(),
            graph_database=self._build_graph_database(),
            storage=self._build_storage(),
            plugin=self._build_plugin(),
        )

    def _build_application(self) -> ApplicationSettings:
        return ApplicationSettings(
            APP_NAME=self._raw.get("APP_NAME", ""),
            APP_VERSION=self._raw.get("APP_VERSION", ""),
            DEBUG=self._raw.get("DEBUG", False),
            PROJECT_ROOT=self._get_project_root(),
        )

    def _build_api(self) -> ApiSettings:
        return ApiSettings(
            HOST=self._raw.get("HOST", ""),
            PORT=self._raw.get("PORT", 0),
            CORS_ORIGINS=self._raw.get("CORS_ORIGINS", []),
            CORS_ALLOW_CREDENTIALS=self._raw.get("CORS_ALLOW_CREDENTIALS", False),
            CORS_ALLOW_METHODS=self._raw.get("CORS_ALLOW_METHODS", []),
            CORS_ALLOW_HEADERS=self._raw.get("CORS_ALLOW_HEADERS", []),
            API_PREFIX=self._raw.get("API_PREFIX", ""),
        )

    def _build_logging(self) -> LoggingSettings:
        return LoggingSettings(
            LOG_LEVEL=self._raw.get("LOG_LEVEL", ""),
            LOG_FORMAT=self._raw.get("LOG_FORMAT", ""),
            LOG_SILENCE_THIRD_PARTY=self._raw.get("LOG_SILENCE_THIRD_PARTY", False),
        )

    def _build_database(self) -> DatabaseSettings:
        return DatabaseSettings(
            DB_URL=self._raw.get("DB_URL", ""),
            DB_POOL_SIZE=self._raw.get("DB_POOL_SIZE", 0),
            DB_MAX_OVERFLOW=self._raw.get("DB_MAX_OVERFLOW", 0),
            DB_ECHO=self._raw.get("DB_ECHO", False),
            DB_TIMEOUT=self._raw.get("DB_TIMEOUT", 0),
        )

    def _build_llm(self) -> LLMSettings:
        return LLMSettings(
            LLM_PROVIDER=self._raw.get("LLM_PROVIDER", ""),
            LLM_API_KEY=self._raw.get("OPENROUTER_API_KEY", ""),
            LLM_BASE_URL=self._raw.get("OPENROUTER_BASE_URL", ""),
            LLM_MODEL=self._raw.get("CHAT_MODEL", ""),
            LLM_TEMPERATURE=self._raw.get("LLM_TEMPERATURE", 0.0),
            LLM_MAX_TOKENS=self._raw.get("LLM_MAX_TOKENS", 0),
            LLM_TIMEOUT=self._raw.get("LLM_TIMEOUT", 0),
            LLM_MAX_RETRIES=self._raw.get("LLM_MAX_RETRIES", 0),
        )

    def _build_vector_database(self) -> VectorDatabaseSettings:
        return VectorDatabaseSettings(
            VECTOR_DB_PROVIDER=self._raw.get("VECTOR_DB_PROVIDER", ""),
            VECTOR_DB_URL=self._raw.get("VECTOR_DB_URL", ""),
            VECTOR_DB_API_KEY=self._raw.get("VECTOR_DB_API_KEY", ""),
            VECTOR_DB_INDEX_NAME=self._raw.get("VECTOR_DB_INDEX_NAME", ""),
            VECTOR_DB_DIMENSION=self._raw.get("VECTOR_DB_DIMENSION", 0),
            VECTOR_DB_METRIC=self._raw.get("VECTOR_DB_METRIC", ""),
        )

    def _build_graph_database(self) -> GraphDatabaseSettings:
        return GraphDatabaseSettings(
            GRAPH_DB_PROVIDER=self._raw.get("GRAPH_DB_PROVIDER", ""),
            GRAPH_DB_URL=self._raw.get("GRAPH_DB_URL", ""),
            GRAPH_DB_USER=self._raw.get("GRAPH_DB_USER", ""),
            GRAPH_DB_PASSWORD=self._raw.get("GRAPH_DB_PASSWORD", ""),
            GRAPH_DB_DATABASE=self._raw.get("GRAPH_DB_DATABASE", ""),
        )

    def _build_storage(self) -> StorageSettings:
        return StorageSettings(
            STORAGE_PROVIDER=self._raw.get("STORAGE_PROVIDER", ""),
            STORAGE_PATH=self._raw.get("STORAGE_PATH", ""),
            STORAGE_BUCKET_NAME=self._raw.get("STORAGE_BUCKET_NAME", ""),
            STORAGE_ACCESS_KEY=self._raw.get("STORAGE_ACCESS_KEY", ""),
            STORAGE_SECRET_KEY=self._raw.get("STORAGE_SECRET_KEY", ""),
            STORAGE_REGION=self._raw.get("STORAGE_REGION", ""),
            STORAGE_ENDPOINT_URL=self._raw.get("STORAGE_ENDPOINT_URL", ""),
        )

    def _build_plugin(self) -> PluginSettings:
        return PluginSettings(
            PLUGIN_ENABLED=self._raw.get("PLUGIN_ENABLED", False),
            PLUGIN_DIRECTORIES=self._raw.get("PLUGIN_DIRECTORIES", ""),
            PLUGIN_ALLOWED=self._raw.get("PLUGIN_ALLOWED", []),
            PLUGIN_BLOCKED=self._raw.get("PLUGIN_BLOCKED", []),
        )

    @staticmethod
    def _get_project_root() -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent
