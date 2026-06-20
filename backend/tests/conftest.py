# Pytest configuration
from __future__ import annotations

import os
import sys

_backend_dir = os.path.join(os.path.dirname(__file__), "..")
_project_root = os.path.join(_backend_dir, "..")
for _p in (_project_root, _backend_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest_plugins: list[str] = []
