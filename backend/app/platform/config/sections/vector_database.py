# vector_database configuration
from __future__ import annotations

from pydantic import BaseModel, Field


class VectorDatabaseSettings(BaseModel):

    VECTOR_DB_PROVIDER: str = Field(
        description="Vector store provider (e.g. pinecone, qdrant, chroma).",
    )
    VECTOR_DB_URL: str = Field(
        description="Connection URL for the vector store.",
    )
    VECTOR_DB_API_KEY: str = Field(
        description="API key for the vector store.",
    )
    VECTOR_DB_INDEX_NAME: str = Field(
        description="Default index / collection name.",
    )
    VECTOR_DB_DIMENSION: int = Field(
        ge=1,
        description="Embedding vector dimension.",
    )
    VECTOR_DB_METRIC: str = Field(
        pattern=r"^(cosine|euclidean|dotproduct)$",
        description="Distance metric for similarity search.",
    )
