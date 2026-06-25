# Application lifespan
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.platform.config.storage import StorageManager
from backend.app.plugins.base import registry
from backend.app.plugins.manifest import ManifestManager
from backend.app.platform.dependencies.container import container

logger = logging.getLogger(__name__)


def _register_plugins() -> None:
    """Load plugins from manifest and register them in the registry."""
    manifest = ManifestManager()
    entries = manifest.load()

    for entry in entries:
        if not entry.enabled:
            logger.info("Plugin '%s' is disabled - skipping.", entry.plugin_type)
            continue

        try:
            import importlib

            if entry.class_path:
                module_path, _, class_name = entry.class_path.rpartition(".")
                module = importlib.import_module(module_path)
                plugin_class = getattr(module, class_name, None)
            else:
                class_path = entry.module
                if "." not in class_path:
                    class_path = f"{entry.module}.extractor"
                module_path, _, class_name = class_path.rpartition(".")
                module = importlib.import_module(f"backend.app.plugins.{module_path}")
                plugin_class = getattr(module, class_name, None)

            if plugin_class is None:
                logger.warning(
                    "Plugin class '%s' not found for module '%s' - skipping.",
                    class_name,
                    entry.module,
                )
                continue

            gateway = (
                container.resolve("ai_gateway")
                if container._services.get("ai_gateway")
                else None
            )
            plugin = plugin_class(ai_gateway=gateway) if gateway else plugin_class()
            registry.register(plugin)
            logger.info("Loaded plugin: %s (%s)", entry.display_name, entry.plugin_type)

        except ImportError as exc:
            logger.warning(
                "Failed to load plugin '%s' for type '%s': %s",
                entry.module,
                entry.plugin_type,
                exc,
            )
        except Exception as exc:
            logger.exception(
                "Unexpected error loading plugin '%s': %s", entry.plugin_type, exc
            )


async def _register_services() -> None:
    """Register shared platform services in the DI container."""
    from backend.app.platform.services.document_detector import DocumentTypeDetector
    from backend.app.platform.services.retrieval import RetrievalService
    from backend.app.platform.services.store_factory import (
        create_graph_store,
        create_vector_store,
    )
    from backend.app.platform.services.vector_store import VectorStore
    from backend.app.agents.ingestion.pipeline import IngestionPipeline
    from backend.app.agents.reasoning.agent import ReasoningAgent

    ai_gateway = container.resolve("ai_gateway")
    if ai_gateway:
        # In-memory vector store for embedding queries
        vector_store = VectorStore(ai_gateway=ai_gateway)
        container.register("vector_store", vector_store)
        logger.info("Registered VectorStore.")

        # Persistent vector store (provider-agnostic, currently Qdrant)
        embedding_store = await create_vector_store()
        container.register("embedding_store", embedding_store)
        logger.info("Registered embedding store (%s).", type(embedding_store).__name__)

        # Persistent graph store (provider-agnostic, currently Neo4j)
        graph_store = await create_graph_store()
        container.register("graph_store", graph_store)
        logger.info("Registered graph store (%s).", type(graph_store).__name__)

        detector = DocumentTypeDetector(ai_gateway=ai_gateway)
        container.register("document_detector", detector)
        logger.info("Registered DocumentTypeDetector.")

        retrieval = RetrievalService(
            vector_store=vector_store,
            graph_store=graph_store,
        )
        container.register("retrieval_service", retrieval)
        logger.info("Registered RetrievalService.")

        reasoning = ReasoningAgent(
            ai_gateway=ai_gateway,
            retrieval_service=retrieval,
        )
        container.register("reasoning_agent", reasoning)
        logger.info("Registered ReasoningAgent.")

        ingestion = IngestionPipeline(
            ai_gateway=ai_gateway,
            vector_store=vector_store,
            embedding_store=embedding_store,
            graph_store=graph_store,
            detector=detector,
        )
        container.register("ingestion_pipeline", ingestion)
        logger.info("Registered IngestionPipeline.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    StorageManager.initialize()
    logger.info("Application startup - initialising databases ...")

    from backend.app.platform.database import close_db, create_tables, init_db

    try:
        init_db()
        await create_tables()
        logger.info("Database tables ready.")
    except Exception as exc:
        logger.warning("PostgreSQL not available (app continues): %s", exc)

    await _register_services()
    logger.info("Services registered.")

    _register_plugins()
    logger.info("Startup complete - %d plugins registered.", len(registry))

    yield

    logger.info("Application shutdown - cleaning up resources ...")
    try:
        await close_db()
    except Exception:
        pass
