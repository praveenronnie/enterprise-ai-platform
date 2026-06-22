from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]

STORAGE_ROOT = PROJECT_ROOT / "storage"
UPLOADS_ROOT = STORAGE_ROOT / "uploads"
TEMP_ROOT = STORAGE_ROOT / "temp"


class StorageManager:
    """Central storage path manager."""

    @staticmethod
    def initialize() -> None:
        for path in (
            STORAGE_ROOT,
            UPLOADS_ROOT,
            TEMP_ROOT,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def base_path(doc_id: str) -> Path:
        path = STORAGE_ROOT / doc_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def document_dir(document_id: str) -> Path:
        path = StorageManager.base_path(document_id) / "documents"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def images_dir(document_id: str) -> Path:
        path = StorageManager.base_path(document_id) / "images"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def tables_dir(document_id: str) -> Path:
        path = StorageManager.base_path(document_id) / "tables"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def doc_json(document_id: str) -> Path:
        return StorageManager.base_path(document_id) / f"{document_id}.json"

    @staticmethod
    def upload_path(filename: str) -> Path:
        return UPLOADS_ROOT / filename
