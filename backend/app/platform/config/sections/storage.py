# storage configuration
from __future__ import annotations

from pydantic import BaseModel, Field


class StorageSettings(BaseModel):

    STORAGE_PROVIDER: str = Field(
        pattern=r"^(local|s3|gcs|azure)$",
        description="Storage backend.",
    )
    STORAGE_PATH: str = Field(
        description="Base directory for local file storage.",
    )
    STORAGE_BUCKET_NAME: str = Field(
        description="Default bucket / container name for cloud providers.",
    )
    STORAGE_ACCESS_KEY: str = Field(
        description="Access key ID (S3 / GCS / Azure).",
    )
    STORAGE_SECRET_KEY: str = Field(
        description="Secret access key.",
    )
    STORAGE_REGION: str = Field(
        description="Region for cloud storage providers.",
    )
    STORAGE_ENDPOINT_URL: str = Field(
        description="Custom endpoint URL (e.g. for MinIO).",
    )
