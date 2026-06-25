"""Shared base model for plugin extraction results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PluginExtractionResult(BaseModel):
    document_type: str = Field(description="Type of document (e.g., resume, logistics)")
    confidence_score: float = Field(
        default=1.0, description="Confidence in extraction accuracy (0.0-1.0)"
    )
    extracted_keywords: list[str] = Field(
        default_factory=list, description="Key terms extracted from document"
    )
    summary: str = Field(
        default="", description="Brief summary of the document content"
    )
    is_graph_eligible: bool = Field(
        default=True,
        description="Whether this extraction should be added to knowledge graph",
    )
