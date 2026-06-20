# AI-specific exceptions
from __future__ import annotations


class AIError(Exception):
    """Base exception for all AI-related errors."""


class ProviderError(AIError):
    """Raised when an external LLM provider returns an error."""


class GatewayError(AIError):
    """Raised when the AI gateway encounters an internal error."""


class EmbeddingError(AIError):
    """Raised when embedding generation fails."""
