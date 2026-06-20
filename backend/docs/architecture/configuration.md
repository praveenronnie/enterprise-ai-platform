# Configuration Architecture

## Overview

The Enterprise AI Platform uses a **composed settings** pattern built on
[Pydantic Settings v2](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
Configuration is split into nine domain-specific section classes, each
responsible for a single concern, and a root `Settings` class that
composes them all.

This design follows the **Single Responsibility Principle** and **Clean
Architecture**: each section can be developed, tested, and extended
independently, and the root class provides a single, immutable entry
point for the entire application.

---

## Configuration Hierarchy

```
Settings  (root — backend.backend.app.platform.config.settings)
│
├── application  →  ApplicationSettings
│   ├── APP_NAME
│   ├── APP_VERSION
│   ├── DEBUG
│   └── PROJECT_ROOT
│
├── api  →  ApiSettings
│   ├── HOST
│   ├── PORT
│   ├── CORS_ORIGINS
│   ├── CORS_ALLOW_CREDENTIALS
│   ├── CORS_ALLOW_METHODS
│   ├── CORS_ALLOW_HEADERS
│   └── API_V1_PREFIX
│
├── logging  →  LoggingSettings
│   ├── LOG_LEVEL
│   ├── LOG_FORMAT
│   └── LOG_SILENCE_THIRD_PARTY
│
├── database  →  DatabaseSettings
│   ├── DB_URL
│   ├── DB_POOL_SIZE
│   ├── DB_MAX_OVERFLOW
│   ├── DB_ECHO
│   └── DB_TIMEOUT
│
├── llm  →  LLMSettings
│   ├── LLM_PROVIDER
│   ├── LLM_API_KEY
│   ├── LLM_BASE_URL
│   ├── LLM_MODEL
│   ├── LLM_TEMPERATURE
│   ├── LLM_MAX_TOKENS
│   ├── LLM_TIMEOUT
│   └── LLM_MAX_RETRIES
│
├── vector_database  →  VectorDatabaseSettings
│   ├── VECTOR_DB_PROVIDER
│   ├── VECTOR_DB_URL
│   ├── VECTOR_DB_API_KEY
│   ├── VECTOR_DB_INDEX_NAME
│   ├── VECTOR_DB_DIMENSION
│   └── VECTOR_DB_METRIC
│
├── graph_database  →  GraphDatabaseSettings
│   ├── GRAPH_DB_PROVIDER
│   ├── GRAPH_DB_URL
│   ├── GRAPH_DB_USER
│   ├── GRAPH_DB_PASSWORD
│   └── GRAPH_DB_DATABASE
│
├── storage  →  StorageSettings
│   ├── STORAGE_PROVIDER
│   ├── STORAGE_LOCAL_PATH
│   ├── STORAGE_BUCKET_NAME
│   ├── STORAGE_ACCESS_KEY
│   ├── STORAGE_SECRET_KEY
│   ├── STORAGE_REGION
│   └── STORAGE_ENDPOINT_URL
│
└── plugin  →  PluginSettings
    ├── PLUGIN_ENABLED
    ├── PLUGIN_DIRECTORIES
    ├── PLUGIN_ALLOWED
    └── PLUGIN_BLOCKED
```

### Backward-Compatible Shortcuts

The root `Settings` class exposes **property shortcuts** for the most
commonly accessed values so that existing code continues to work without
modification:

| Shortcut property | Delegates to |
|---|---|
| `settings.APP_NAME` | `settings.application.APP_NAME` |
| `settings.APP_VERSION` | `settings.application.APP_VERSION` |
| `settings.DEBUG` | `settings.application.DEBUG` |
| `settings.PROJECT_ROOT` | `settings.application.PROJECT_ROOT` |
| `settings.HOST` | `settings.api.HOST` |
| `settings.PORT` | `settings.api.PORT` |
| `settings.CORS_ORIGINS` | `settings.api.CORS_ORIGINS` |
| `settings.CORS_ALLOW_CREDENTIALS` | `settings.api.CORS_ALLOW_CREDENTIALS` |
| `settings.CORS_ALLOW_METHODS` | `settings.api.CORS_ALLOW_METHODS` |
| `settings.CORS_ALLOW_HEADERS` | `settings.api.CORS_ALLOW_HEADERS` |
| `settings.LOG_LEVEL` | `settings.logging.LOG_LEVEL` |
| `settings.LOG_FORMAT` | `settings.logging.LOG_FORMAT` |

New code should prefer the section-qualified access pattern:

```python
# Preferred (section-qualified)
db_url = settings.database.DB_URL
llm_model = settings.llm.LLM_MODEL

# Still works (backward-compatible shortcut)
debug = settings.DEBUG
```

---

## Loading Process

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Startup                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  _load_env_files(env)          │
              │                               │
              │  1. .env.shared  ──────────────│── (common to all envs)
              │  2. .env.{env}  ───────────────│── (env-specific)
              │  3. .env        ───────────────│── (local overrides)
              │                               │
              │  load_dotenv(..., override=True)│
              └───────────┬───────────────────┘
                          │
                          ▼
              ┌───────────────────────────────┐
              │  os.environ is now populated  │
              └───────────┬───────────────────┘
                          │
                          ▼
              ┌───────────────────────────────┐
              │  Settings() instantiated       │
              │                               │
              │  Pydantic reads from           │
              │  os.environ for root fields    │
              │  (e.g. ENVIRONMENT)            │
              │                               │
              │  Each section is created via   │
              │  default_factory, which also   │
              │  reads from os.environ         │
              └───────────┬───────────────────┘
                          │
                          ▼
              ┌───────────────────────────────┐
              │  settings singleton ready      │
              │  (frozen, immutable)           │
              └───────────────────────────────┘
```

### Key Design Decisions

1. **Single env-loading point**: The `_load_env_files()` function is
   called **once** at module level, before the `Settings` singleton is
   instantiated.  All section classes have `env_file=None` so they never
   re-read ``.env`` files.

2. **No external DI library**: The root class composes sections via
   plain `default_factory` — no dependency injection container is
   required.

3. **Immutability**: Every section class and the root class use
   `frozen=True`.  After startup, no part of the configuration can be
   mutated.

---

## Environment Strategy

### Supported Environments

| Environment | Purpose | Default `.env` file |
|---|---|---|
| `development` | Local development | `.env.development` |
| `testing` | Automated tests (CI) | `.env.testing` |
| `production` | Production deployment | `.env.production` |

### File Loading Order

Files are loaded in the following order (later files override earlier
ones):

1. **`.env.shared`** — Values common to all environments (e.g. cloud
   provider endpoints, shared API prefixes).  Should be committed to
   version control.

2. **`.env.{ENVIRONMENT}`** — Environment-specific overrides (e.g.
   `DEBUG=false` in production, test database URLs).  Should be
   committed to version control.

3. **`.env`** — Local overrides (e.g. developer-specific API keys,
   local paths).  **Must be gitignored**.

### Selecting the Environment

Set the `ENVIRONMENT` environment variable:

```bash
# Development (default)
export ENVIRONMENT=development

# Testing
export ENVIRONMENT=testing

# Production
export ENVIRONMENT=production
```

If `ENVIRONMENT` is not set, the system defaults to `development`.

### Example: Production Setup

```bash
# .env.shared (committed)
LLM_MAX_TOKENS=4096
VECTOR_DB_DIMENSION=1536

# .env.production (committed)
DEBUG=false
DB_URL=postgresql+asyncpg://user:pass@prod-db:5432/enterprise-ai
LLM_API_KEY=${LLM_API_KEY}   # resolved from CI/CD secrets

# .env (gitignored — not used in production, but shown for completeness)
# (empty in production — all values come from .env.shared + .env.production + env vars)
```

---

## Adding a New Configuration Section

1. Create a new file in `backend/app/platform/config/sections/` (e.g.
   `search.py` for a search engine provider).

2. Define a `BaseSettings` subclass with `env_file=None` and
   `frozen=True`:

   ```python
   from __future__ import annotations
   from typing import ClassVar
   from pydantic import Field
   from pydantic_settings import BaseSettings, SettingsConfigDict

   class SearchSettings(BaseSettings):
       SEARCH_PROVIDER: str = Field(default="elasticsearch")
       SEARCH_URL: str = Field(default="http://localhost:9200")

       model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
           env_file=None,
           extra="ignore",
           frozen=True,
       )
   ```

3. Add the new class to `sections/__init__.py`.

4. Add a field to the root `Settings` class in `settings.py`:

   ```python
   search: SearchSettings = Field(
       default_factory=SearchSettings,
       description="Search engine configuration.",
   )
   ```

5. Add corresponding environment variables to `.env.example`.

No other changes are required — the loading, validation, and
immutability mechanisms are inherited automatically.

---

## File Locations

| File | Purpose |
|---|---|
| `backend/app/platform/config/settings.py` | Root `Settings` class, `_load_env_files()`, singleton |
| `backend/app/platform/config/__init__.py` | Public API exports |
| `backend/app/platform/config/sections/` | Domain-specific section classes |
| `backend/.env.example` | Documented example of all env vars |
| `backend/.env.shared` | (optional) Shared env values |
| `backend/.env.development` | (optional) Dev overrides |
| `backend/.env.testing` | (optional) Test overrides |
| `backend/.env.production` | (optional) Production overrides |
| `backend/.env` | Local overrides (gitignored) |