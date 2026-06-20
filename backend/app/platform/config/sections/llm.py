# llm configuration
from __future__ import annotations

from pydantic import BaseModel, Field


class LLMSettings(BaseModel):

    LLM_PROVIDER: str = Field(
        description="Provider name (e.g. openai, anthropic, azure, ollama).",
    )
    LLM_API_KEY: str = Field(
        description="API key for the LLM provider. Required in production.",
    )
    LLM_BASE_URL: str = Field(
        description="Base URL for the provider API (empty uses provider default).",
    )
    LLM_MODEL: str = Field(
        description="Default model identifier.",
    )
    LLM_TEMPERATURE: float = Field(
        ge=0.0,
        le=2.0,
        description="Sampling temperature.",
    )
    LLM_MAX_TOKENS: int = Field(
        ge=1,
        description="Maximum tokens per request.",
    )
    LLM_TIMEOUT: int = Field(
        ge=1,
        description="Request timeout in seconds.",
    )
    LLM_MAX_RETRIES: int = Field(
        ge=0,
        description="Maximum number of retry attempts on failure.",
    )
    LLM_EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformers model for embeddings.",
    )
