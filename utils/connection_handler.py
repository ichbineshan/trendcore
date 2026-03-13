from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import loaded_config
from config.logging import logger


class ConnectionHandler:
    """Handles database connection and session management."""

    def __init__(self, connection_manager=None):
        self._session: Optional[AsyncSession] = None
        self._connection_manager = connection_manager

    @property
    def session(self):
        if not self._session:
            session_factory = self._connection_manager.get_session_factory()
            self._session = session_factory()
        return self._session

    async def session_commit(self):
        await self.session.commit()

    async def close(self):
        if self._session:
            await self._session.close()


@asynccontextmanager
async def get_connection_handler_for_app():
    """Get connection handler for the main database."""
    from utils.load_config import ensure_connection_manager_initialized
    await ensure_connection_manager_initialized()

    connection_handler = ConnectionHandler(
        connection_manager=loaded_config.connection_manager
    )
    try:
        yield connection_handler
    finally:
        await connection_handler.close()


async def get_connection_handler_for_app_dependency():
    """Dependency injection for FastAPI routes."""
    from utils.load_config import ensure_connection_manager_initialized
    await ensure_connection_manager_initialized()

    connection_handler = ConnectionHandler(
        connection_manager=loaded_config.connection_manager
    )
    try:
        yield connection_handler
    finally:
        await connection_handler.close()
