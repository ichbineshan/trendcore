"""
Style Generation Temporal Worker.
"""

import sys

from temporalio.client import Client
from temporalio.worker import Worker

from styles.temporal.constants import TemporalQueue
from styles.temporal.workflow import StyleGenerationWorkflow
from styles.temporal.activities import (
    trigger_style_generation_activity,
    mark_style_failed_activity,
)
from config.settings import loaded_config
from utils.temporal.worker_registry import register_worker


@register_worker("style_generation_worker")
async def style_generation_worker():
    """Run the style generation Temporal worker."""
    try:
        print("STYLE_WORKER: Starting worker function...", file=sys.stderr, flush=True)

        print(f"STYLE_WORKER: Connecting to Temporal at {loaded_config.temporal_host}...", file=sys.stderr, flush=True)
        client = await Client.connect(loaded_config.temporal_host)
        print("STYLE_WORKER: Connected to Temporal.", file=sys.stderr, flush=True)

        print("STYLE_WORKER: Creating Worker...", file=sys.stderr, flush=True)
        worker = Worker(
            client,
            task_queue=TemporalQueue.STYLE_GENERATION.value,
            workflows=[StyleGenerationWorkflow],
            activities=[
                trigger_style_generation_activity,
                mark_style_failed_activity,
            ],
        )
        print("STYLE_WORKER: Worker created.", file=sys.stderr, flush=True)

        print(f"STYLE_WORKER: Listening on queue: {TemporalQueue.STYLE_GENERATION.value}", file=sys.stderr, flush=True)
        await worker.run()
    except Exception as e:
        import traceback
        print(f"STYLE_WORKER: ERROR - {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        print("STYLE_WORKER: Full traceback:", file=sys.stderr, flush=True)
        traceback.print_exc()
        raise
