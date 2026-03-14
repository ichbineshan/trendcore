from asyncio import current_task

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_scoped_session,
    AsyncSession,
)
from sqlalchemy.orm import sessionmaker



class ConnectionManager:

    def __init__(self, db_url, db_echo):
        self.db_url = db_url
        self.db_echo = db_echo
        self._db_engine, self._db_session_factory = self._setup_db()

    def get_session_factory(self):
        return self._db_session_factory

    def _setup_db(self):
        engine = create_async_engine(
            str(self.db_url),
            echo=self.db_echo,
            pool_size=10,  # Increased from 10 to 20
            max_overflow=20,  # Allow up to 30 additional connections
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_timeout=30,  # Wait up to 30 seconds for a connection
            pool_reset_on_return='commit',  # Reset connection state on return
        )
        session_factory = async_scoped_session(
            sessionmaker(
                engine,
                expire_on_commit=False,
                class_=AsyncSession,
            ),
            scopefunc=current_task,
        )
        return engine, session_factory

    async def close_connections(self):
        await self._db_engine.dispose()
