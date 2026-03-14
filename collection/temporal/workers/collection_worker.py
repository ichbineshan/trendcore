"""
Collection Generation Temporal Worker.
"""

import logging
import sys

from temporalio.client import Client
from temporalio.worker import Worker

from collection.temporal.constants import TemporalQueue
from collection.temporal.workflow import CollectionGenerationWorkflow
from collection.temporal.activities import (
    generate_overview_activity,
    update_collection_completed_activity,
    update_collection_failed_activity,
)
from config.settings import loaded_config
from utils.temporal.worker_registry import register_worker

logger = logging.getLogger(__name__)

@register_worker("generate_collection_worker")
async def generate_collection_worker():
    """Run the collection generation Temporal worker."""
    try:
        print("COLLECTION_WORKER: Starting worker function...", file=sys.stderr, flush=True)

        print(f"COLLECTION_WORKER: Connecting to Temporal at {loaded_config.temporal_host}...", file=sys.stderr, flush=True)
        client = await Client.connect(loaded_config.temporal_host)
        print("COLLECTION_WORKER: Connected to Temporal.", file=sys.stderr, flush=True)

        print("COLLECTION_WORKER: Creating Worker...", file=sys.stderr, flush=True)
        worker = Worker(
            client,
            task_queue=TemporalQueue.COLLECTION_GENERATION.value,
            workflows=[CollectionGenerationWorkflow],
            activities=[
                generate_overview_activity,
                update_collection_completed_activity,
                update_collection_failed_activity,
            ],
        )
        print("COLLECTION_WORKER: Worker created.", file=sys.stderr, flush=True)

        print(f"COLLECTION_WORKER: Listening on queue: {TemporalQueue.COLLECTION_GENERATION.value}", file=sys.stderr, flush=True)
        await worker.run()
    except Exception as e:
        import traceback
        print(f"COLLECTION_WORKER: ERROR - {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        print("COLLECTION_WORKER: Full traceback:", file=sys.stderr, flush=True)
        traceback.print_exc()
        raise

