"""
"temporal" :: Health Check.

This is required by K8s to ensure consumer pod doesn't die.
"""

import asyncio
import logging

import aiofiles


from utils.load_config import init_connections
from utils.temporal.constants import (
    HEALTH_CHECK_CONSUMER_TIME,
    HEALTH_CHECK_FILENAME,
    HEALTH_CHECK_LOG_INFO_MESSAGE,
    READY_CHECK_CONSUMER_TIME,
    READY_CHECK_FILENAME,
    READY_CHECK_LOG_INFO_MESSAGE
)
from utils.temporal.worker_registry import get_all_workers

logger = logging.getLogger(__name__)


async def _healthz():
    """Perform health check on consumer every 30 seconds."""
    while True:
        async with aiofiles.open(HEALTH_CHECK_FILENAME, 'w') as out:
            await out.write(' ')
            await out.flush()
            logger.debug(HEALTH_CHECK_LOG_INFO_MESSAGE)
        await asyncio.sleep(HEALTH_CHECK_CONSUMER_TIME)


async def _readyz():
    """Perform ready check on consumer every 30 seconds."""
    while True:
        async with aiofiles.open(READY_CHECK_FILENAME, 'w') as out:
            await out.write(' ')
            await out.flush()
            logger.debug(READY_CHECK_LOG_INFO_MESSAGE)
        await asyncio.sleep(READY_CHECK_CONSUMER_TIME)


async def run_worker(worker_name: str):
    """Run the Temporal worker for scheduled tasks."""
    await init_connections()

    workers = get_all_workers()
    
    worker = workers.get(worker_name)
    if worker:
        asyncio.create_task(worker())
    else:
        print(f"Worker with name: {worker_name} not registered!")
        return

    asyncio.create_task(_healthz())
    asyncio.create_task(_readyz())

    all_tasks = asyncio.all_tasks()
    executed_tasks = asyncio.gather(*all_tasks, return_exceptions=True)
    results = await executed_tasks
    for result in results:
        if isinstance(result, Exception):
            print(f"Exception in a task: {result}")