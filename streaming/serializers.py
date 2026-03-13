from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class StreamEventType(str, Enum):
    """Stream event types for SSE."""
    THREAD_CREATED = "thread_created"
    USER_MESSAGE_CREATED = "user_message_created"
    STREAM_START = "stream_start"
    CONTENT_CHUNK = "content_chunk"
    STREAM_COMPLETE = "stream_complete"
    STREAM_END = "stream_end"
    ERROR = "error"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class QuestionSchema(BaseModel):
    """Schema for chat question/message."""
    message: str = Field(..., description="The user's message")
    thread_id: Optional[UUID] = Field(None, description="Existing thread ID")
    parent_message_id: Optional[UUID] = Field(None, description="Parent message ID for threading")
    images: Optional[List[str]] = Field(None, description="List of image URLs")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class StreamEvent(BaseModel):
    """Schema for stream events."""
    type: StreamEventType
    content: str
    thread_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    metadata: Optional[dict] = None
