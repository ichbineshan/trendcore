"""
Moodboard Image Generation Temporal Worker.

Dedicated worker with limited concurrency to stay within
Vertex AI rate limits (10 images/min).
"""

import sys

from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

from image_generation.temporal.constants import TemporalQueue
from image_generation.temporal.workflow import MoodboardImageWorkflow
from image_generation.temporal.activities import (
    fetch_moodboard_data_activity,
    generate_collage_image_activity,
    generate_element_images_activity,
    mark_images_completed_activity,
    mark_images_failed_activity,
)
from config.settings import loaded_config
from utils.temporal.worker_registry import register_worker


@register_worker("moodboard_image_worker")
async def moodboard_image_worker():
    """
    Run the moodboard image generation Temporal worker.

    Uses max_concurrent_activities=2 to stay within Vertex AI rate limits.
    """
    try:
        print("MOODBOARD_IMAGE_WORKER: Starting worker function...", file=sys.stderr, flush=True)

        temporal_host = loaded_config.temporal_host or "localhost:7233"
        temporal_namespace = loaded_config.temporal_namespace

        print(
            f"MOODBOARD_IMAGE_WORKER: Connecting to Temporal at {temporal_host}...",
            file=sys.stderr,
            flush=True,
        )

        client = await Client.connect(
            target_host=temporal_host,
            namespace=temporal_namespace,
        )
        print("MOODBOARD_IMAGE_WORKER: Connected to Temporal.", file=sys.stderr, flush=True)

        print("MOODBOARD_IMAGE_WORKER: Creating Worker...", file=sys.stderr, flush=True)

        worker = Worker(
            client,
            task_queue=TemporalQueue.MOODBOARD_IMAGE_GENERATION.value,
            workflows=[MoodboardImageWorkflow],
            activities=[
                fetch_moodboard_data_activity,
                generate_collage_image_activity,
                generate_element_images_activity,
                mark_images_completed_activity,
                mark_images_failed_activity,
            ],
           # max_concurrent_activities=2,  # Rate limiting for Vertex AI
            workflow_runner=SandboxedWorkflowRunner(
                restrictions=SandboxRestrictions.default.with_passthrough_all_modules()
            ),
        )

        print("MOODBOARD_IMAGE_WORKER: Worker created.", file=sys.stderr, flush=True)
        print(
            f"MOODBOARD_IMAGE_WORKER: Listening on queue: {TemporalQueue.MOODBOARD_IMAGE_GENERATION.value}",
            file=sys.stderr,
            flush=True,
        )

        await worker.run()

    except Exception as e:
        import traceback

        print(
            f"MOODBOARD_IMAGE_WORKER: ERROR - {type(e).__name__}: {e}",
            file=sys.stderr,
            flush=True,
        )
        print("MOODBOARD_IMAGE_WORKER: Full traceback:", file=sys.stderr, flush=True)
        traceback.print_exc()
        raise
