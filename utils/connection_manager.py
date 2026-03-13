from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from config.logging import logger


class ConnectionManager:
    """Manages database connections using SQLAlchemy async engine."""

    def __init__(self, db_url: str, db_echo: bool = False):
        self.db_url = db_url
        self.db_echo = db_echo
        self._engine = None
        self._session_factory = None

    def get_engine(self):
        """Get or create the async engine."""
        if not self._engine:
            self._engine = create_async_engine(
                self.db_url,
                echo=self.db_echo,
                poolclass=NullPool,
                pool_pre_ping=True,
            )
            logger.info("Database engine created", db_url=self.db_url)
        return self._engine

    def get_session_factory(self):
        """Get or create the session factory."""
        if not self._session_factory:
            engine = self.get_engine()
            self._session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            logger.info("Session factory created")
        return self._session_factory

    async def close(self):
        """Close the database engine."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine disposed")
