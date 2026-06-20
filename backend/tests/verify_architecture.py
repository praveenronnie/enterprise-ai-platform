# verify_architecture tests
from __future__ import annotations

import os
import sys

_backend_dir = os.path.join(os.path.dirname(__file__), "..")
_project_root = os.path.join(_backend_dir, "..")
for _p in (_project_root, _backend_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from pydantic import BaseModel

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

assert issubclass(Settings, BaseModel), "Settings must inherit from BaseModel"
print("✓ Settings inherits from BaseModel")

section_classes = [
    ("ApiSettings", ApiSettings),
    ("ApplicationSettings", ApplicationSettings),
    ("DatabaseSettings", DatabaseSettings),
    ("GraphDatabaseSettings", GraphDatabaseSettings),
    ("LLMSettings", LLMSettings),
    ("LoggingSettings", LoggingSettings),
    ("PluginSettings", PluginSettings),
    ("StorageSettings", StorageSettings),
    ("VectorDatabaseSettings", VectorDatabaseSettings),
]
for name, cls in section_classes:
    assert issubclass(cls, BaseModel), f"{name} must inherit from BaseModel"
    print(f"✓ {name} inherits from BaseModel")

s = Settings(
    application=ApplicationSettings(
        APP_NAME="test", APP_VERSION="1.0", DEBUG=False, PROJECT_ROOT="/tmp"
    ),
    api=ApiSettings(
        HOST="0.0.0.0",
        PORT=8000,
        CORS_ORIGINS=["*"],
        CORS_ALLOW_CREDENTIALS=True,
        CORS_ALLOW_METHODS=["*"],
        CORS_ALLOW_HEADERS=["*"],
        API_V1_PREFIX="/api/v1",
    ),
    logging=LoggingSettings(
        LOG_LEVEL="INFO", LOG_FORMAT="test", LOG_SILENCE_THIRD_PARTY=True
    ),
    database=DatabaseSettings(
        DB_URL="sqlite:///test.db",
        DB_POOL_SIZE=5,
        DB_MAX_OVERFLOW=10,
        DB_ECHO=False,
        DB_TIMEOUT=30,
    ),
    llm=LLMSettings(
        LLM_PROVIDER="openai",
        LLM_API_KEY="",
        LLM_BASE_URL="",
        LLM_MODEL="gpt-4",
        LLM_TEMPERATURE=0.7,
        LLM_MAX_TOKENS=4096,
        LLM_TIMEOUT=60,
        LLM_MAX_RETRIES=3,
    ),
    vector_database=VectorDatabaseSettings(
        VECTOR_DB_PROVIDER="chroma",
        VECTOR_DB_URL="",
        VECTOR_DB_API_KEY="",
        VECTOR_DB_INDEX_NAME="default",
        VECTOR_DB_DIMENSION=1536,
        VECTOR_DB_METRIC="cosine",
    ),
    graph_database=GraphDatabaseSettings(
        GRAPH_DB_PROVIDER="neo4j",
        GRAPH_DB_URL="bolt://localhost:7687",
        GRAPH_DB_USER="neo4j",
        GRAPH_DB_PASSWORD="",
        GRAPH_DB_DATABASE="neo4j",
    ),
    storage=StorageSettings(
        STORAGE_PROVIDER="local",
        STORAGE_LOCAL_PATH="/tmp",
        STORAGE_BUCKET_NAME="test",
        STORAGE_ACCESS_KEY="",
        STORAGE_SECRET_KEY="",
        STORAGE_REGION="us-east-1",
        STORAGE_ENDPOINT_URL="",
    ),
    plugin=PluginSettings(
        PLUGIN_ENABLED=True,
        PLUGIN_DIRECTORIES="./plugins",
        PLUGIN_ALLOWED=[],
        PLUGIN_BLOCKED=[],
    ),
)
try:
    s.APP_NAME = "changed"
    assert False, "Settings should be frozen!"
except Exception:
    print("✓ Settings is frozen (immutable)")

assert s.APP_NAME == "test"
assert s.APP_VERSION == "1.0"
assert s.DEBUG is False
assert s.HOST == "0.0.0.0"
assert s.PORT == 8000
assert s.LOG_LEVEL == "INFO"
print("✓ Shortcut properties work correctly")

assert s.application.APP_NAME == "test"
assert s.api.HOST == "0.0.0.0"
assert s.logging.LOG_LEVEL == "INFO"
assert s.database.DB_URL == "sqlite:///test.db"
assert s.llm.LLM_PROVIDER == "openai"
assert s.vector_database.VECTOR_DB_PROVIDER == "chroma"
assert s.graph_database.GRAPH_DB_PROVIDER == "neo4j"
assert s.storage.STORAGE_PROVIDER == "local"
assert s.plugin.PLUGIN_ENABLED is True
print("✓ Section access works correctly")

print("\n✅ All architecture checks passed!")
