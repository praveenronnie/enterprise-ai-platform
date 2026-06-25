"""Reasoning agent - handles chat, retrieval, and multi-hop graph reasoning."""

from __future__ import annotations

import json
import logging
from typing import Any

from backend.app.platform.ai.gateway import AIGateway
from backend.app.platform.ai.prompts.common import REASONING_PROMPT
from backend.app.platform.ai.schemas import ChatMessage, GenerateRequest
from backend.app.platform.services.retrieval import RetrievalResult, RetrievalService

logger = logging.getLogger(__name__)


class ReasoningAgent:
    def __init__(
        self,
        ai_gateway: AIGateway,
        retrieval_service: RetrievalService,
    ) -> None:
        self._gateway = ai_gateway
        self._retrieval = retrieval_service

    async def chat(
        self,
        question: str,
        top_k: int = 5,
        include_graph: bool = True,
        document_id: str | None = None,
    ) -> dict[str, Any]:
        results = await self._retrieval.retrieve(
            query=question,
            top_k=top_k,
            include_graph=include_graph,
            document_id=document_id,
        )

        if not results:
            return {
                "answer": "I could not find any relevant documents to answer your question.",
                "sources": [],
                "result_count": 0,
            }

        context_parts: list[str] = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Chunk {i}] Document: {result.chunk.document_id}")
            context_parts.append(f"Text: {result.chunk.text[:500]}")
            if result.chunk.metadata:
                context_parts.append(f"Metadata: {json.dumps(result.chunk.metadata)}")
            if result.graph_context:
                context_parts.append(f"Graph context: {json.dumps(result.graph_context, indent=2)}")
            context_parts.append("---")

        context_str = "\n".join(context_parts)
        prompt = REASONING_PROMPT.format(context=context_str, question=question)
        request = GenerateRequest(
            messages=[ChatMessage(role="system", content=prompt)],
            temperature=0.3,
            max_tokens=2000,
        )

        response = await self._gateway.generate(request)

        sources = []
        for result in results:
            source = {
                "document_id": result.chunk.document_id,
                "text_preview": result.chunk.text[:200],
                "metadata": result.chunk.metadata,
            }
            if result.graph_context:
                source["graph_entities"] = [ctx.get("name", "") for ctx in result.graph_context[:3]]
            sources.append(source)

        return {
            "answer": response.content,
            "sources": sources,
            "result_count": len(results),
        }

    async def analyze(
        self,
        question: str,
        document_id: str,
    ) -> dict[str, Any]:
        return await self.chat(
            question=question,
            document_id=document_id,
            top_k=10,
            include_graph=True,
        )

    async def compare(
        self,
        question: str,
        document_ids: list[str],
    ) -> dict[str, Any]:
        all_results: list[RetrievalResult] = []
        for doc_id in document_ids:
            results = await self._retrieval.retrieve(
                query=question,
                top_k=3,
                include_graph=True,
                document_id=doc_id,
            )
            all_results.extend(results)

        context_parts: list[str] = []
        for i, result in enumerate(all_results, 1):
            context_parts.append(f"[Source {i}] Document: {result.chunk.document_id}")
            context_parts.append(f"Text: {result.chunk.text[:500]}")
            if result.graph_context:
                context_parts.append(f"Graph: {json.dumps(result.graph_context, indent=2)}")
            context_parts.append("---")

        context_str = "\n".join(context_parts)
        prompt = REASONING_PROMPT.format(context=context_str, question=question)

        request = GenerateRequest(
            messages=[ChatMessage(role="system", content=prompt)],
            temperature=0.3,
            max_tokens=2000,
        )
        response = await self._gateway.generate(request)

        return {
            "answer": response.content,
            "documents_analyzed": document_ids,
            "sources_used": len(all_results),
        }