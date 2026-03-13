from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from threads.models import Thread, ThreadMessage, Task
from config.logging import logger


class ThreadDAO:
    """Data Access Object for Thread operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_thread(self, thread: Thread) -> Thread:
        """Create a new thread."""
        self.session.add(thread)
        await self.session.flush()
        await self.session.refresh(thread)
        logger.info(f"Thread created: {thread.id}")
        return thread

    async def get_thread_by_id(self, thread_id: UUID) -> Optional[Thread]:
        """Get a thread by ID."""
        result = await self.session.execute(
            select(Thread).where(Thread.id == thread_id)
        )
        return result.scalar_one_or_none()

    async def get_threads_by_user(
        self, user_id: str, org_id: str, offset: int = 0, limit: int = 10
    ) -> List[Thread]:
        """Get threads for a specific user with pagination."""
        result = await self.session.execute(
            select(Thread)
            .where(Thread.user_id == user_id, Thread.org_id == org_id)
            .order_by(desc(Thread.updated_at))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_thread(self, thread_id: UUID) -> bool:
        """Delete a thread by ID."""
        result = await self.session.execute(
            delete(Thread).where(Thread.id == thread_id)
        )
        await self.session.flush()
        return result.rowcount > 0


class ThreadMessageDAO:
    """Data Access Object for ThreadMessage operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_message(self, message: ThreadMessage) -> ThreadMessage:
        """Create a new message."""
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        logger.info(f"Message created: {message.id}")
        return message

    async def get_message_by_id(self, message_id: UUID) -> Optional[ThreadMessage]:
        """Get a message by ID."""
        result = await self.session.execute(
            select(ThreadMessage).where(ThreadMessage.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_messages_by_thread(
        self, thread_id: UUID, limit: int = 100
    ) -> List[ThreadMessage]:
        """Get all messages for a thread."""
        result = await self.session.execute(
            select(ThreadMessage)
            .where(ThreadMessage.thread_uuid == thread_id)
            .order_by(ThreadMessage.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())


class TaskDAO:
    """Data Access Object for Task operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task: Task) -> Task:
        """Create a new task."""
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        logger.info(f"Task created: {task.id}")
        return task

    async def get_active_task_for_thread(self, thread_id: UUID) -> Optional[Task]:
        """Get active task for a thread."""
        result = await self.session.execute(
            select(Task)
            .where(Task.thread_id == thread_id, Task.status == "pending")
            .order_by(desc(Task.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_task_status(self, task_id: UUID, status: str):
        """Update task status."""
        task = await self.session.get(Task, task_id)
        if task:
            task.status = status
            await self.session.flush()
            logger.info(f"Task {task_id} status updated to {status}")
