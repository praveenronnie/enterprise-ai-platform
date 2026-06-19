# =============================================================================
# Enterprise AI Platform — Backend Dockerfile
# =============================================================================
# Multi-stage build: install dependencies in a separate stage to keep the
# final image lean.
# =============================================================================

# ── Stage 1: Dependencies ────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv for fast dependency resolution.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy only the dependency metadata first for better layer caching.
COPY pyproject.toml .

# Install production dependencies.
RUN uv sync --no-dev --frozen

# ── Stage 2: Runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy the installed virtual environment from the builder stage.
COPY --from=builder /app/.venv /app/.venv

# Copy application source code.
COPY app/ /app/app/

# Use the virtual environment's Python.
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose the application port.
EXPOSE 8000

# Health check (requires curl in the image).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health').raise_for_status()"

# Run the application with uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]