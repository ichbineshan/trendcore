from fastapi import APIRouter

from streaming.views import stream_chat

streaming_router = APIRouter(prefix="/streaming", tags=["AI Streaming"])

streaming_router.add_api_route(
    "/chat",
    methods=["POST"],
    endpoint=stream_chat,
    description="Stream AI Chat Response",
)
