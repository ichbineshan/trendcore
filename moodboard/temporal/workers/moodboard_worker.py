"""
Moodboard Generation Temporal Worker.
"""

import sys

from temporalio.client import Client
from temporalio.worker import Worker

from moodboard.temporal.constants import TemporalQueue
from moodboard.temporal.workflow import MoodboardGenerationWorkflow
from moodboard.temporal.activities import (
    create_moodboard_record_activity,
    generate_collage_prompt_activity,
    split_into_elements_activity,
    mark_moodboard_completed_activity,
    mark_moodboard_failed_activity,
)
from config.settings import loaded_config
from utils.temporal.worker_registry import register_worker


@register_worker("moodboard_generation_worker")
async def moodboard_generation_worker():
    """Run the moodboard generation Temporal worker."""
    try:
        print("MOODBOARD_WORKER: Starting worker function...", file=sys.stderr, flush=True)

        print(f"MOODBOARD_WORKER: Connecting to Temporal at {loaded_config.temporal_host}...", file=sys.stderr, flush=True)
        client = await Client.connect(loaded_config.temporal_host)
        print("MOODBOARD_WORKER: Connected to Temporal.", file=sys.stderr, flush=True)

        print("MOODBOARD_WORKER: Creating Worker...", file=sys.stderr, flush=True)
        worker = Worker(
            client,
            task_queue=TemporalQueue.MOODBOARD_GENERATION.value,
            workflows=[MoodboardGenerationWorkflow],
            activities=[
                create_moodboard_record_activity,
                generate_collage_prompt_activity,
                split_into_elements_activity,
                mark_moodboard_completed_activity,
                mark_moodboard_failed_activity,
            ],
        )
        print("MOODBOARD_WORKER: Worker created.", file=sys.stderr, flush=True)

        print(f"MOODBOARD_WORKER: Listening on queue: {TemporalQueue.MOODBOARD_GENERATION.value}", file=sys.stderr, flush=True)
        await worker.run()
    except Exception as e:
        import traceback
        print(f"MOODBOARD_WORKER: ERROR - {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        print("MOODBOARD_WORKER: Full traceback:", file=sys.stderr, flush=True)
        traceback.print_exc()
        raise
