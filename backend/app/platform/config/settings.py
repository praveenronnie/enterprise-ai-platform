# Application settings
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

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


class Settings(BaseModel):

    application: ApplicationSettings = Field(
        description="Application metadata & runtime flags.",
    )
    api: ApiSettings = Field(
        description="HTTP server & API configuration.",
    )
    logging: LoggingSettings = Field(
        description="Logging subsystem configuration.",
    )
    database: DatabaseSettings = Field(
        description="Relational database connection parameters.",
    )
    llm: LLMSettings = Field(
        description="Large Language Model provider settings.",
    )
    vector_database: VectorDatabaseSettings = Field(
        description="Vector database (embedding store) settings.",
    )
    graph_database: GraphDatabaseSettings = Field(
        description="Graph database connection parameters.",
    )
    storage: StorageSettings = Field(
        description="File / object storage configuration.",
    )
    plugin: PluginSettings = Field(
        description="Plugin subsystem configuration.",
    )

    @property
    def APP_NAME(self) -> str:
        return self.application.APP_NAME

    @property
    def APP_VERSION(self) -> str:
        return self.application.APP_VERSION

    @property
    def DEBUG(self) -> bool:
        return self.application.DEBUG

    @property
    def PROJECT_ROOT(self) -> Path:
        return self.application.PROJECT_ROOT

    @property
    def HOST(self) -> str:
        return self.api.HOST

    @property
    def PORT(self) -> int:
        return self.api.PORT

    @property
    def CORS_ORIGINS(self) -> list[str]:
        return self.api.CORS_ORIGINS

    @property
    def CORS_ALLOW_CREDENTIALS(self) -> bool:
        return self.api.CORS_ALLOW_CREDENTIALS

    @property
    def CORS_ALLOW_METHODS(self) -> list[str]:
        return self.api.CORS_ALLOW_METHODS

    @property
    def CORS_ALLOW_HEADERS(self) -> list[str]:
        return self.api.CORS_ALLOW_HEADERS

    @property
    def API_PREFIX(self) -> str:
        return self.api.API_PREFIX

    @property
    def LOG_LEVEL(self) -> str:
        return self.logging.LOG_LEVEL

    @property
    def LOG_FORMAT(self) -> str:
        return self.logging.LOG_FORMAT

    model_config = {
        "frozen": True,
        "extra": "ignore",
    }
