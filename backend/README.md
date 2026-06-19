# Enterprise AI Platform — Backend

Production-ready foundation for an Enterprise AI Platform built with **FastAPI** and **Python 3.11+**.

## Architecture

```
backend/
├── app/
│   ├── api/            # Route definitions (HTTP layer)
│   │   └── v1/         # API version 1 endpoints
│   ├── core/           # Application lifecycle, logging, exception handlers
│   ├── config/         # Pydantic Settings (env-based configuration)
│   ├── plugins/        # Plugin system (extensible AI capabilities)
│   ├── services/       # Business logic / use cases
│   ├── repositories/   # Data access layer
│   ├── models/         # Domain entities
│   ├── schemas/        # Pydantic models (request/response serialization)
│   ├── middleware/     # ASGI middleware (CORS, etc.)
│   ├── utils/          # Utility helpers
│   └── dependencies/   # FastAPI dependency injection wiring
├── tests/              # Pytest test suite
├── scripts/            # Development runner scripts
├── docs/               # Documentation
├── Dockerfile          # Multi-stage Docker build
├── .env.example        # Environment variable template
└── pyproject.toml      # Project metadata and dependencies
```

This follows **Clean Architecture** and **SOLID** principles:

- **Single Responsibility**: Each module has one clearly defined purpose.
- **Open/Closed**: The plugin system allows extending functionality without modifying existing code.
- **Dependency Inversion**: High-level modules depend on abstractions (interfaces), not concrete implementations.
- **Separation of Concerns**: API layer, business logic, and data access are strictly separated.

## Quick Start

### Prerequisites

- Python 3.11+ (recommended: 3.11)
- [uv](https://docs.astral.sh/uv/) (fast Python package manager)

### Local Development

```bash
cd backend

# Create virtual environment and install dependencies
uv sync

# Copy environment configuration
cp .env.example .env

# Run in development mode (with hot-reload)
uvicorn app.main:app --reload --port 8000

# Or use the PowerShell runner
.\scripts\run.ps1
```

The API will be available at **http://localhost:8000**.

Swagger docs are available at **http://localhost:8000/docs** (only in `DEBUG=true` mode).

ReDoc is available at **http://localhost:8000/redoc** (only in `DEBUG=true` mode).

### Docker

```bash
cd backend
docker compose up --build
```

## API Endpoints

| Method | Path              | Description          |
|--------|-------------------|----------------------|
| GET    | `/api/v1/health`  | Health check / liveness probe |
| GET    | `/api/v1/version` | Application version metadata |

### GET /api/v1/health

```json
{
  "status": "ok",
  "timestamp": "2026-06-19T11:00:00Z",
  "version": "0.1.0"
}
```

### GET /api/v1/version

```json
{
  "name": "Enterprise AI Platform",
  "version": "0.1.0",
  "description": "Enterprise AI Document Intelligence Platform"
}
```

## Testing

```bash
cd backend
uv sync --dev
pytest -v
```

## Configuration

All configuration is managed through environment variables (see `.env.example`):

| Variable                 | Default                        | Description                |
|--------------------------|--------------------------------|----------------------------|
| `APP_NAME`               | Enterprise AI Platform         | Application name           |
| `APP_VERSION`            | 0.1.0                          | Semantic version           |
| `DEBUG`                  | false                          | Enable debug mode          |
| `HOST`                   | 0.0.0.0                        | Server bind address        |
| `PORT`                   | 8000                           | Server port                |
| `CORS_ORIGINS`           | ["*"]                          | Allowed CORS origins       |
| `LOG_LEVEL`              | INFO                           | Logging level              |
| `LOG_FORMAT`             | ...                            | Log format string          |

## Project Status

This is the **foundation** layer — no business logic, authentication, plugins,
databases, or AI features are implemented yet. These will be added incrementally.