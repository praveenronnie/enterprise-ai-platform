# Environment loader
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class EnvironmentLoader:

    def __init__(self) -> None:
        self._loaded: bool = False
        self._raw_config: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        if self._loaded:
            return self._raw_config

        self._load_dotenv()
        self._raw_config = self._snapshot_env()
        self._loaded = True
        return self._raw_config

    def _load_dotenv(self) -> None:
        project_root = self._find_project_root()
        env_path = project_root / ".env"

        if not env_path.is_file():
            raise FileNotFoundError(
                f".env file not found at {env_path}. "
                f"Copy .env.example to .env and configure it for your environment."
            )

        load_dotenv(env_path, override=True)

    @staticmethod
    def _snapshot_env() -> dict[str, Any]:
        return dict(os.environ)

    @staticmethod
    def _find_project_root() -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent
