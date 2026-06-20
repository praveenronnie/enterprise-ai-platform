# Pydantic schemas for AI operations
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


class ChatMessage(BaseModel):
    role: str = Field(description="Message role: system, user, or assistant.")
    content: str = Field(description="Message text content.")


class GenerateRequest(BaseModel):
    messages: list[ChatMessage] = Field(description="Conversation history.")
    model: str | None = Field(default=None, description="Override default model.")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)


class GenerateResponse(BaseModel):
    content: str = Field(description="Generated text content.")
    model: str = Field(description="Model used for generation.")
    usage: dict[str, Any] = Field(
        default_factory=dict, description="Token usage stats."
    )


class EmbeddingRequest(BaseModel):
    texts: list[str] = Field(description="Texts to embed.", min_length=1)
    model: str | None = Field(
        default=None, description="Override default embedding model."
    )


class EmbeddingResponse(BaseModel):
    embeddings: list[list[float]] = Field(description="Generated embedding vectors.")
    model: str = Field(description="Model used for embeddings.")
    dimensions: int = Field(description="Embedding vector dimensions.")


class ChatRequest(BaseModel):
    message: str = Field(description="User message.")


class ChatResponse(BaseModel):
    response: str = Field(description="Generated response.")
