from typing import Any, Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateThreadRequest(BaseModel):
    title: str
    user_id: str | None = None
    org_id: str | None = None
    meta: dict | None = None
    user_email: str | None = None


class CreateMessageRequest(BaseModel):
    role: str
    content: list | dict
    thread_uuid: UUID | None = None
    parent_message_id: UUID | None = None
    prompt_details: dict | None = None
    images: list | None = None
    user_query: str | None = None
    metadata: dict | None = {}


class ThreadSchema(BaseModel):
    id: UUID
    title: str
    user_id: str | None = None
    created_at: int
    updated_at: int
    last_message_id: UUID | None = None
    meta: dict[str, Any] | None = None
    org_id: str | None = None
    task_status: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ThreadMessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_message_id: UUID | None = None
    content: list | dict | None = None
    role: str
    prompt_details: dict | None = None
    images: list | dict | None = None
    user_query: Optional[str] = None
    meta_data: Optional[dict] = {}


class ThreadQueryParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")
    query: str | None = Field(None, description="Search query for thread messages")
