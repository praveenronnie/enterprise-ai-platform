# Dependency injection container
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Generator
from typing import Any

from fastapi import Request

from backend.app.platform.config.settings import Settings

logger = logging.getLogger(__name__)


class DIContainer:

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, key: str, instance: object) -> None:
        self._services[key] = instance
        logger.debug("Registered service: %s (%s)", key, type(instance).__name__)

    def resolve(self, key: str) -> object:
        if key not in self._services:
            raise KeyError(f"Service '{key}' is not registered")
        return self._services[key]


container: DIContainer = DIContainer()


SERVICE_SETTINGS = "settings"


def get_container() -> Generator[DIContainer, None, None]:
    yield container


def get_settings() -> Generator[Settings, None, None]:
    if SERVICE_SETTINGS not in container._services:
        from backend.app.platform.config import ConfigurationManager, EnvironmentLoader

        loader = EnvironmentLoader()
        raw_config = loader.load()
        config_manager = ConfigurationManager(raw_config)
        settings = config_manager.build()
        container.register(SERVICE_SETTINGS, settings)
    else:
        settings = container.resolve(SERVICE_SETTINGS)

    yield settings


def register_ai_services(settings: Settings) -> None:
    from backend.app.platform.ai.embeddings import EmbeddingService
    from backend.app.platform.ai.gateway import AIGateway
    from backend.app.platform.ai.providers.openrouter import OpenRouterProvider

    provider = OpenRouterProvider(
        api_key=settings.llm.LLM_API_KEY,
        base_url=settings.llm.LLM_BASE_URL,
        model=settings.llm.LLM_MODEL,
        timeout=settings.llm.LLM_TIMEOUT,
        max_retries=settings.llm.LLM_MAX_RETRIES,
    )
    container.register("openrouter_provider", provider)

    embedding_service = EmbeddingService(
        model_name=settings.llm.LLM_EMBEDDING_MODEL,
    )
    container.register("embedding_service", embedding_service)

    gateway = AIGateway(
        provider=provider,
        embedding_service=embedding_service,
    )
    container.register("ai_gateway", gateway)


async def get_request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", "")


def get_ai_gateway() -> Generator:
    yield container.resolve("ai_gateway")
