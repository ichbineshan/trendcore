import uuid
from typing import List, Optional

from sqlalchemy.orm.attributes import flag_modified

from threads.dao import ThreadDAO, ThreadMessageDAO, TaskDAO
from threads.exceptions import ThreadNotFoundError, ThreadMessageNotFoundError
from threads.models import Thread, ThreadMessage, Task, Role
from threads.serializers import (
    CreateThreadRequest,
    CreateMessageRequest,
    ThreadSchema,
    ThreadMessageSchema,
)
from utils.connection_handler import ConnectionHandler
from config.logging import logger


class ThreadService:
    """Service layer for thread operations."""

    def __init__(self, connection_handler: ConnectionHandler):
        self.connection_handler = connection_handler
        self.thread_dao = ThreadDAO(connection_handler.session)
        self.message_dao = ThreadMessageDAO(connection_handler.session)
        self.task_dao = TaskDAO(connection_handler.session)

    async def create_thread(
        self, request: CreateThreadRequest, user_id: str, org_id: str, user_email: str
    ) -> Thread:
        """Create a new thread."""
        thread = Thread(
            id=uuid.uuid4(),
            title=request.title,
            user_id=user_id,
            org_id=org_id,
            user_email=user_email,
            meta=request.meta or {},
        )

        thread = await self.thread_dao.create_thread(thread)
        await self.connection_handler.session_commit()
        logger.info(f"Thread created successfully: {thread.id}")
        return thread

    async def get_thread(self, thread_id: uuid.UUID) -> Thread:
        """Get a thread by ID."""
        thread = await self.thread_dao.get_thread_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(str(thread_id))
        return thread

    async def get_threads(
        self, user_id: str, org_id: str, page: int = 1, page_size: int = 10
    ) -> List[ThreadSchema]:
        """Get paginated threads for a user."""
        offset = (page - 1) * page_size
        threads = await self.thread_dao.get_threads_by_user(
            user_id, org_id, offset, page_size
        )

        # Convert to schema and include task status
        thread_schemas = []
        for thread in threads:
            task = await self.task_dao.get_active_task_for_thread(thread.id)
            thread_schema = ThreadSchema.model_validate(thread)
            thread_schema.task_status = task.status if task else None
            thread_schemas.append(thread_schema)

        return thread_schemas

    async def delete_thread(self, thread_id: uuid.UUID):
        """Delete a thread."""
        # Check if thread exists
        await self.get_thread(thread_id)

        deleted = await self.thread_dao.delete_thread(thread_id)
        await self.connection_handler.session_commit()

        if not deleted:
            raise ThreadNotFoundError(str(thread_id))

        logger.info(f"Thread deleted successfully: {thread_id}")

    async def create_message(
        self, request: CreateMessageRequest, thread_id: uuid.UUID
    ) -> ThreadMessage:
        """Create a new message in a thread."""
        # Ensure thread exists
        await self.get_thread(thread_id)

        message = ThreadMessage(
            id=uuid.uuid4(),
            thread_uuid=thread_id,
            parent_message_id=request.parent_message_id,
            content=request.content,
            role=Role(request.role),
            prompt_details=request.prompt_details or {},
            images=request.images or [],
            user_query=request.user_query,
            meta_data=request.metadata or {},
        )

        message = await self.message_dao.create_message(message)
        await self.connection_handler.session_commit()
        logger.info(f"Message created successfully: {message.id}")
        return message

    async def get_thread_messages(
        self, thread_id: uuid.UUID
    ) -> List[ThreadMessageSchema]:
        """Get all messages for a thread."""
        # Ensure thread exists
        await self.get_thread(thread_id)

        messages = await self.message_dao.get_messages_by_thread(thread_id)
        return [ThreadMessageSchema.model_validate(msg) for msg in messages]

    async def get_collection_brief_history(self, thread_id: uuid.UUID) -> list[dict]:
        """
        Build chat-friendly history for a collection brief thread.

        Returns a list of message dicts that the frontend can use to rehydrate
        chat state (text + forms) for the given thread.
        """
        history: list[dict] = []
        # Use raw ORM models here so we can access created_at/updated_at directly
        messages = await self.message_dao.get_messages_by_thread(thread_id)

        for msg in messages:
            meta = (msg.meta_data or {}).get("collection_brief") if getattr(msg, "meta_data", None) else None

            # Derive role as 'user' | 'assistant'
            raw_role = getattr(msg, "role", None)
            role_value = getattr(raw_role, "value", None) or str(raw_role or "").lower()

            # Base shape
            record: dict = {
                "id": str(msg.id),
                "role": role_value,
                "timestamp": getattr(msg, "created_at", None),
                "formSchema": None,
                "questionMetadata": None,
                "isReviewAndFinish": False,
                "submitLabel": None,
            }

            if meta:
                # Assistant-side, chat-friendly snapshot
                record["role"] = meta.get("role", record["role"])
                record["content"] = meta.get("content", "")
                record["formSchema"] = meta.get("formSchema")
                record["questionMetadata"] = meta.get("questionMetadata")
                record["isReviewAndFinish"] = meta.get("isReviewAndFinish", False)
                record["submitLabel"] = meta.get("submitLabel")
            else:
                # User messages (and any non-collection-brief system messages)
                content = getattr(msg, "content", None)
                text: str = ""
                if isinstance(content, dict):
                    # e.g. {"text": "..."}
                    text = str(content.get("text", ""))
                elif isinstance(content, list) and content:
                    # e.g. [{"content": "..."}]
                    first = content[0]
                    if isinstance(first, dict):
                        text = str(first.get("content", ""))
                    else:
                        text = str(first)
                record["content"] = text

            history.append(record)

        return history

    async def get_active_task_for_thread(self, thread_id: uuid.UUID) -> Optional[Task]:
        """Get active task for a thread."""
        return await self.task_dao.get_active_task_for_thread(thread_id)

    async def update_thread_meta(self, thread_id: uuid.UUID, meta: dict) -> Thread:
        """Update thread metadata."""
        thread = await self.get_thread(thread_id)
        thread.meta = meta
        flag_modified(thread, "meta")
        await self.connection_handler.session_commit()
        logger.info(f"Thread meta updated successfully: {thread_id}")
        return thread
