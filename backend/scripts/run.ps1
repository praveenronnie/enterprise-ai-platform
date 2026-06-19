# =============================================================================
# Development runner for the Enterprise AI Platform backend (PowerShell).
# =============================================================================

$ErrorActionPreference = "Stop"

# Activate virtual environment if it exists.
if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
}

Write-Host "==> Starting backend on http://0.0.0.0:8000"
Write-Host "==> API docs at http://localhost:8000/docs (DEBUG mode only)"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload