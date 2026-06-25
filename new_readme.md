# Enterprise AI Document Processing Platform

## Multi-Agent Graph RAG System

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI (REST API)                   │
│  /upload  /chat  /plugins  /health  /ai  /documents     │
└────────────────────┬────────────────────────────────────┘
                      │
┌────────────────────▼────────────────────────────────────┐
│                   DI Container                          │
│   (AIGateway, VectorStore, GraphStore, ReasoningAgent)  │
└────────────────────┬────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌──────────────────┐   ┌──────────────────┐
│  Plugin System   │   │  Service Layer   │
│  ┌────────────┐  │   │  ┌────────────┐  │
│  │ Registry   │  │   │  │ Detector   │  │
│  │ Manifest   │  │   │  │ VectorStore│  │
│  │ Resume     │  │   │  │ GraphStore │  │
│  │ Logistics  │  │   │  │ Retrieval  │  │
│  └────────────┘  │   │  └────────────┘  │
└──────────────────┘   └──────────────────┘
          │                       │
          ▼                       ▼
┌─────────────────────────────────────────────────────────┐
│                    Agents                               │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐   │
│  │ Ingestion  │  │ Reasoning  │  │  Orchestrator    │   │
│  │ Pipeline   │  │ Agent      │  │  (multi-agent)   │   │
│  └────────────┘  └────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## System Components

### 1. Plugin System (`backend/app/plugins/`)
- **`base.py`** - `DocumentPlugin` ABC + `PluginRegistry` singleton
- **`base_models.py`** - Shared `PluginExtractionResult` base model
- **`manifest.py`** - `ManifestManager` reads/writes `manifest.json`
- **`manifest.json`** - Plugin definitions with output_model references
- **`resume/`** - Resume/CV parsing plugin
  - `models.py` - Pydantic v2 models (ResumeExtraction, Experience, Education)
  - `extractor.py` - Extraction logic with validated model output
  - `manifest.py` - Plugin manifest with output_model reference
- **`logistics/`** - Logistics document plugin
  - `models.py` - Pydantic v2 models (LogisticsExtraction, ShipmentItem)
  - `extractor.py` - Extraction logic with validated model output
  - `manifest.py` - Plugin manifest with output_model reference

### 2. Services (`backend/app/platform/services/`)
- **`document_detector.py`** - LLM-based document type classifier
- **`vector_store.py`** - In-memory vector store with cosine similarity
- **`graph_store.py`** - In-memory knowledge graph with BFS traversal
- **`retrieval.py`** - Combines vector search + graph context for RAG
- **`store_factory.py`** - Factory for creating provider-specific stores (Qdrant, Neo4j)
- **`qdrant_store.py`** - Qdrant persistent vector store implementation
- **`neo4j_store.py`** - Neo4j persistent graph store implementation

### 3. Agents (`backend/app/agents/`)
- **`ingestion/pipeline.py`** - Incremental 7-step pipeline with duplicate detection and chunk-level diff
- **`reasoning/agent.py`** - RAG agent with multi-hop graph reasoning
- **`orchestrator.py`** - Multi-agent orchestration coordinator
- **`base/`** - Agent base classes and interfaces

### 4. API Endpoints (`backend/app/platform/api/v1/`)
- **`plugins.py`** - CRUD: `GET/POST/DELETE/PUT /plugins`
- **`chat.py`** - `POST /chat`, `/chat/analyze`, `/chat/compare`
- **`document.py`** - `POST /documents/upload`
- **`ai.py`** - AI gateway endpoints
- **`health.py`** - Health check endpoints
- **`version.py`** - Version information endpoints

### 5. Core Infrastructure
- **`lifespan.py`** - Registers services and plugins at startup
- **`main.py`** - FastAPI app with all routers mounted
- **`container.py`** - DI container
- **`database.py`** - Async database session factory (PostgreSQL + SQLAlchemy)
- **`middleware/cors.py`** - CORS configuration

### 6. Data Layer (`backend/app/shared/`)
- **`models/models.py`** - Domain models (Chunk.content_hash added)
- **`repositories/document_repository.py`** - In-memory document store keyed by binary_hash
- **`repositories/__init__.py`** - Repository exports
- **`utils/chunk_differ.py`** - Chunk-level diff engine
- **`utils/helpers.py`** - Shared utility functions
- **`services/document_processor.py`** - Docling-based document processing
- **`schemas/`** - Shared Pydantic schemas

### 7. Platform Models (`backend/app/platform/models/`)
- **`document.py`** - SQLAlchemy document model for PostgreSQL

### 8. Shared Prompts (`backend/app/platform/ai/prompts/`)
- **`common.py`** - Common prompts (DETECTION_PROMPT, REASONING_PROMPT) used across services and agents

### 9. Configuration (`backend/app/platform/config/`)
- **`loader.py`** - Environment variable loader
- **`manager.py`** - Configuration manager
- **`sections/`** - Configuration section models (vector_database, etc.)
- **`storage.py`** - Storage manager for database initialization

## Plugin Structure (Pydantic v2)

Each plugin follows this structure:

```
plugins/
├── base_models.py          # Shared PluginExtractionResult base
├── resume/
│   ├── __init__.py
│   ├── models.py           # Pydantic v2 models
│   ├── extractor.py        # Plugin implementation
│   └── manifest.py         # Plugin manifest with output_model
└── logistics/
    ├── __init__.py
    ├── models.py           # Pydantic v2 models
    ├── extractor.py        # Plugin implementation
    └── manifest.py         # Plugin manifest with output_model
```

## Adding a New Plugin

### Method 1: Via API (Runtime)
```bash
curl -X POST http://localhost:8000/api/v1/plugins
```

### Method 2: Via Filesystem
1. Create `backend/app/plugins/medical/` with `models.py`, `extractor.py`, `manifest.py`
2. Define Pydantic v2 models inheriting from `PluginExtractionResult`
3. Add entry to `backend/app/plugins/manifest.json`
4. Restart the application

## Ingestion Flow (Incremental)

1. **Upload** -> Docling processes PDF
2. **Duplicate Detection** -> Check binary_hash against DocumentRepository
3. **Detect** -> LLM classifies document type
4. **Extract** -> Plugin extracts structured data using Pydantic v2 models
5. **Chunk Diff** -> Compare new chunks with previously indexed version
6. **Vector Delta** -> Only upsert/insert/remove changed vectors
7. **Graph Delta** -> Only upsert/remove changed entities/relations

## Retrieval Flow
1. **Query** -> User asks a question via `/chat`
2. **Search** -> Vector store finds top-k similar chunks
3. **Graph Context** -> Related entities are fetched via BFS
4. **Generate** -> LLM generates answer with context + graph
5. **Response** -> Answer with sources and graph entities returned

## Incremental Ingestion Design

### Duplicate Detection
- Uses Docling's `binary_hash` (already stored in Document model)
- `DocumentRepository.find_by_binary_hash()` checks if exact same file was already indexed
- If found: **zero writes** - returns "already indexed" response immediately

### Chunk-Level Diff
- Each chunk has a `content_hash` (SHA-256 of chunk text)
- `ChunkDiffer.diff_chunks()` compares old vs new chunks by index and content_hash
- Output: unchanged, updated, inserted, removed lists

### Vector Store Delta
- **Unchanged**: skipped entirely
- **Updated**: `upsert_chunk()` removes old entry, embeds and inserts new
- **Inserted**: `add_chunks()` only for new chunks
- **Removed**: `remove_chunks()` by chunk_id list

### Graph Store Delta
- **Entities**: old vs new entity_id sets determine what to remove vs upsert
- **Relations**: old vs new (source, target, type) sets determine delta
- `sync_document_graph()` handles all four cases in one call

## Database Layer

### PostgreSQL (Primary Storage)
- **`backend/app/platform/database.py`** - Async SQLAlchemy engine and session management
- **`backend/app/platform/models/document.py`** - Document ORM model
- Supports connection pooling, async sessions, and automatic table creation
- Configured via `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`

### Vector Stores
- **In-Memory** (`VectorStore`) - For embedding queries and similarity search
- **Qdrant** (`QdrantVectorStore`) - Persistent vector store for production
- Provider-agnostic via `store_factory.py`

### Graph Stores
- **In-Memory** (`GraphStore`) - For graph traversal and BFS
- **Neo4j** (`Neo4jGraphStore`) - Persistent graph database for production
- Provider-agnostic via `store_factory.py`

## Project Structure
```
backend/
├── app/
│   ├── agents/
│   │   ├── ingestion/pipeline.py   # Incremental ingestion
│   │   ├── reasoning/agent.py      # RAG + graph reasoning
│   │   ├── orchestrator.py         # Multi-agent orchestration
│   │   └── base/                   # Agent base classes
│   ├── plugins/
│   │   ├── base.py                 # DocumentPlugin + PluginRegistry
│   │   ├── base_models.py          # Shared PluginExtractionResult
│   │   ├── manifest.py             # ManifestManager
│   │   ├── manifest.json           # Plugin definitions
│   │   ├── resume/                 # Resume plugin package
│   │   │   ├── models.py
│   │   │   ├── extractor.py
│   │   │   └── manifest.py
│   │   └── logistics/              # Logistics plugin package
│   │       ├── models.py
│   │       ├── extractor.py
│   │       └── manifest.py
│   ├── platform/
│   │   ├── ai/
│   │   │   ├── gateway.py          # AI gateway
│   │   │   ├── schemas.py          # Request/response models
│   │   │   ├── providers/          # AI provider implementations
│   │   │   │   └── openrouter.py   # OpenRouter integration
│   │   │   └── prompts/
│   │   │       └── common.py       # Shared prompts
│   │   ├── api/v1/                 # REST endpoints
│   │   │   ├── ai.py               # AI endpoints
│   │   │   ├── chat.py             # Chat endpoints
│   │   │   ├── document.py         # Document upload
│   │   │   ├── health.py           # Health checks
│   │   │   ├── plugins.py          # Plugin CRUD
│   │   │   └── version.py          # Version info
│   │   ├── config/                 # Configuration
│   │   │   ├── loader.py           # Environment loader
│   │   │   ├── manager.py          # Config manager
│   │   │   ├── storage.py          # Storage manager
│   │   │   └── sections/           # Config sections
│   │   ├── core/
│   │   │   ├── lifespan.py         # Startup registration
│   │   │   ├── exceptions.py       # Exception handlers
│   │   │   └── logging.py          # Logging setup
│   │   ├── dependencies/
│   │   │   └── container.py        # DI container
│   │   ├── middleware/
│   │   │   └── cors.py             # CORS setup
│   │   ├── models/
│   │   │   └── document.py         # SQLAlchemy document model
│   │   ├── services/               # Business services
│   │   │   ├── document_detector.py
│   │   │   ├── vector_store.py
│   │   │   ├── graph_store.py
│   │   │   ├── retrieval.py
│   │   │   ├── store_factory.py
│   │   │   ├── qdrant_store.py
│   │   │   └── neo4j_store.py
│   │   └── database.py             # DB session factory
│   └── shared/
│       ├── models/
│       │   └── models.py           # Domain models
│       ├── repositories/           # Data repositories
│       │   └── document_repository.py
│       ├── schemas/                # Pydantic schemas
│       ├── services/               # Shared services
│       │   └── document_processor.py
│       └── utils/                  # Utilities
│           ├── chunk_differ.py
│           └── helpers.py
├── tests/                          # Test suite
│   ├── conftest.py                 # Pytest configuration
│   ├── test_health.py              # Health endpoint tests
│   ├── test_version.py             # Version endpoint tests
│   ├── test_plugin_system.py       # Plugin framework tests
│   └── verify_architecture.py      # Architecture verification
└── README.md
```

## Running the Application
```bash
cd backend
docker compose up --build
# or
uvicorn backend.app.main:app --reload
```

## API Documentation (when DEBUG=true)
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing
```bash
# Run all tests
cd backend && pytest tests/

# Run specific test file
cd backend && pytest tests/test_plugin_system.py -v

# Run with coverage
cd backend && pytest tests/ --cov=backend.app --cov-report=html
```

## Environment Configuration
Key environment variables:
- `AI_GATEWAY__PROVIDER` - AI provider (openrouter, openai, etc.)
- `AI_GATEWAY__API_KEY` - API key for AI provider
- `VECTOR_DB_PROVIDER` - Vector store provider (qdrant)
- `GRAPH_DB_PROVIDER` - Graph store provider (neo4j)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD` - PostgreSQL config
- `DEBUG` - Enable debug mode (shows docs, detailed errors)