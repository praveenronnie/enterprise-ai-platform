"""Simple factory that returns a concrete vector/graph store based on env config."""

from __future__ import annotations

from backend.app.platform.config.loader import EnvironmentLoader
from backend.app.platform.services.graph_store import GraphStoreBase
from backend.app.platform.services.neo4j_store import Neo4jGraphStore
from backend.app.platform.services.qdrant_store import QdrantVectorStore
from backend.app.platform.services.vector_store import VectorStoreBase


async def create_vector_store() -> VectorStoreBase:
    """Return a VectorStoreBase instance based on VECTOR_DB_PROVIDER."""
    env = EnvironmentLoader().load()
    provider = env.get("VECTOR_DB_PROVIDER", "qdrant")
    if provider == "qdrant":
        store = QdrantVectorStore(env=env)
        await store.ensure_collection()
        return store
    raise ValueError(f"Unsupported vector store provider: {provider}")


async def create_graph_store() -> GraphStoreBase:
    """Return a GraphStoreBase instance based on GRAPH_DB_PROVIDER."""
    env = EnvironmentLoader().load()
    provider = env.get("GRAPH_DB_PROVIDER", "neo4j")
    if provider == "neo4j":
        return Neo4jGraphStore(env=env)
    raise ValueError(f"Unsupported graph store provider: {provider}")
