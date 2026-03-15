"""
Postgres checkpointer retry utilities (same pattern as cortex).

Use get_async_postgres_saver_with_retry(conn_string) when creating the collection brief
agent so checkpoint state is stored per thread in PostgreSQL.
"""
import asyncio
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from config.logging import logger


@asynccontextmanager
async def get_async_postgres_saver_with_retry(
    conn_string: str, max_retries: int = 3, base_delay: float = 2.0
):
    """
    Get AsyncPostgresSaver with retry logic for connection failures (same as cortex).

    Args:
        conn_string: PostgreSQL connection string
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff

    Yields:
        AsyncPostgresSaver: PostgreSQL saver instance
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        entered = False
        try:
            async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
                entered = True
                yield checkpointer
                return
        except Exception as e:
            if entered:
                raise

            last_exception = e
            logger.debug(
                "AsyncPostgresSaver connection failed (attempt %s/%s): %s: %s",
                attempt + 1,
                max_retries + 1,
                type(e).__name__,
                str(e),
            )

            if attempt < max_retries:
                delay = base_delay * (2**attempt)
                logger.warning(
                    "AsyncPostgresSaver connection failed, retrying in %ss (attempt %s/%s): %s",
                    delay,
                    attempt + 1,
                    max_retries + 1,
                    str(e),
                )
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(
                    "AsyncPostgresSaver connection failed after %s attempts: %s",
                    max_retries + 1,
                    str(e),
                )
                raise last_exception

    if last_exception:
        raise last_exception
