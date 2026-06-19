#!/usr/bin/env bash
# =============================================================================
# Development runner for the Enterprise AI Platform backend.
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

# Activate virtual environment if it exists.
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "==> Starting backend on http://0.0.0.0:8000"
echo "==> API docs at http://localhost:8000/docs (DEBUG mode only)"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload