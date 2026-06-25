"""Chat and retrieval API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.agents.reasoning.agent import ReasoningAgent
from backend.app.platform.dependencies.container import container

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response Models ──────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message / question.")
    top_k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve.")
    include_graph: bool = Field(True, description="Include knowledge graph context.")
    document_id: str | None = Field(None, description="Filter to a specific document.")


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]
    result_count: int


class AnalyzeRequest(BaseModel):
    question: str = Field(..., description="Question to analyze.")
    document_id: str = Field(..., description="Document ID to analyze.")


class CompareRequest(BaseModel):
    question: str = Field(..., description="Question to compare across documents.")
    document_ids: list[str] = Field(
        ..., min_length=2, description="Document IDs to compare."
    )


# ── Dependency ─────────────────────────────────────────────────────────────


def get_reasoning_agent() -> ReasoningAgent:
    agent = container.resolve("reasoning_agent")
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reasoning agent not available.",
        )
    return agent


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent: ReasoningAgent = Depends(get_reasoning_agent),
) -> ChatResponse:
    """Ask a question and get an answer with RAG + graph context."""
    result = await agent.chat(
        question=request.message,
        top_k=request.top_k,
        include_graph=request.include_graph,
        document_id=request.document_id,
    )
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        result_count=result["result_count"],
    )


@router.post("/chat/analyze", response_model=ChatResponse)
async def analyze_document(
    request: AnalyzeRequest,
    agent: ReasoningAgent = Depends(get_reasoning_agent),
) -> ChatResponse:
    """Deep analysis of a specific document."""
    result = await agent.analyze(
        question=request.question,
        document_id=request.document_id,
    )
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        result_count=result["result_count"],
    )


@router.post("/chat/compare", response_model=dict[str, Any])
async def compare_documents(
    request: CompareRequest,
    agent: ReasoningAgent = Depends(get_reasoning_agent),
) -> dict[str, Any]:
    """Compare information across multiple documents."""
    return await agent.compare(
        question=request.question,
        document_ids=request.document_ids,
    )
