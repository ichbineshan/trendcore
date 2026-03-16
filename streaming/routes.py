from fastapi import APIRouter

from streaming.views import stream_chat, get_collection_brief_history

streaming_router = APIRouter(prefix="/streaming", tags=["AI Streaming"])

streaming_router.add_api_route(
    "/chat",
    methods=["POST"],
    endpoint=stream_chat,
    description="Stream AI Chat Response",
)

streaming_router.add_api_route(
    "/collection-brief/threads/{thread_id}/history",
    methods=["GET"],
    endpoint=get_collection_brief_history,
    description="Get collection brief chat history for a thread",
)
