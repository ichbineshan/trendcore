from config.settings import loaded_config
from config.logging import logger
from utils.connection_manager import ConnectionManager
from utils.redis_client import RedisClient


async def init_connections():
    """Initialize database and Redis connections."""
    logger.info("Initializing database connection manager")

    loaded_config.connection_manager = ConnectionManager(
        db_url=loaded_config.db_url,
        db_echo=loaded_config.db_echo
    )

    logger.info("Connection manager initialized successfully")


async def ensure_connection_manager_initialized():
    """Ensure the connection manager is initialized before use."""
    if loaded_config.connection_manager is None:
        logger.info("Connection manager not initialized, initializing now...")
        await init_connections()


async def run_on_startup():
    """Run initialization tasks on application startup."""
    logger.info("Running startup tasks")
    await init_connections()
    logger.info("Startup tasks completed")


async def run_on_exit():
    """Run cleanup tasks on application shutdown."""
    logger.info("Running shutdown tasks")

    if loaded_config.connection_manager:
        await loaded_config.connection_manager.close()
        logger.info("Database connection closed")

    logger.info("Shutdown tasks completed")
