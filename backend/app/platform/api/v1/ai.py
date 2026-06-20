# AI integration test endpoint
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.platform.ai.gateway import AIGateway
from backend.app.platform.ai.schemas import ChatRequest, ChatResponse
from backend.app.platform.dependencies.container import get_ai_gateway

router = APIRouter()


@router.post(
    "/ai/chat",
    response_model=ChatResponse,
    summary="AI chat integration test",
    description="Sends a message through the full AI Gateway pipeline.",
    tags=["ai"],
)
async def chat(
    request: ChatRequest,
    gateway: AIGateway = Depends(get_ai_gateway),
) -> ChatResponse:
    from backend.app.platform.ai.schemas import ChatMessage, GenerateRequest

    generate_request = GenerateRequest(
        messages=[
            ChatMessage(role="system", content="You are a helpful AI assistant."),
            ChatMessage(role="user", content=request.message),
        ],
    )
    result = await gateway.generate(generate_request)
    return ChatResponse(response=result.content)