import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Callable, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import (
    OperationalError,
    DisconnectionError,
    TimeoutError as SQLAlchemyTimeoutError,
    ResourceClosedError,
    InvalidRequestError
)

from config.settings import loaded_config

from config.logging import logger


class ConnectionHandler:

    def __init__(self, connection_manager=None, event_bridge=None):
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
    connection_handler = ConnectionHandler(
        connection_manager=loaded_config.connection_manager
    )
    try:
        yield connection_handler
    finally:
        await connection_handler.close()


@asynccontextmanager
async def get_connection_handler_for_locksmith():
    connection_handler = ConnectionHandler(
        connection_manager=loaded_config.connection_manager_locksmith
    )
    try:
        yield connection_handler
    finally:
        await connection_handler.close()

