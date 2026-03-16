import uuid

from fastapi import Depends
from fastapi.responses import StreamingResponse

from streaming.exceptions import (
    StreamingError,
    StreamGenerationError,
    AgentConfigurationError,
    StreamingServiceError,
)
from streaming.serializers import QuestionSchema
from streaming.services import StreamingService
from utils.common import handle_exceptions
from utils.connection_handler import (
    ConnectionHandler,
    get_connection_handler_for_app_dependency,
)
from threads.services import ThreadService


@handle_exceptions(
    "Failed to stream response",
    [StreamingError, StreamGenerationError, AgentConfigurationError, StreamingServiceError],
)
async def stream_chat(
    question_schema: QuestionSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app_dependency),
):
    """Stream AI chat responses."""
    streaming_service = StreamingService(connection_handler)

    if question_schema.images and len(question_schema.images) > 4:
        raise StreamingError(message="Maximum 4 images allowed")

    return StreamingResponse(
        streaming_service.generate_streaming_response(question_schema),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@handle_exceptions(
    "Failed to fetch collection brief history",
    [StreamingError, StreamingServiceError],
)
async def get_collection_brief_history(
    thread_id: str,
    connection_handler: ConnectionHandler = Depends(
        get_connection_handler_for_app_dependency
    ),
):
    """
    Return chat-friendly messages for a collection brief thread so the frontend
    can rehydrate history after refresh.
    """
    thread_service = ThreadService(connection_handler)
    history = await thread_service.get_collection_brief_history(
        uuid.UUID(thread_id)
    )

    return {"thread_id": thread_id, "messages": history}

