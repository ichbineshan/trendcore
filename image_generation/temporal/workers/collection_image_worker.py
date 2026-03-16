"""
Collection Image Generation Temporal Worker.

Dedicated worker for generating collection hero/banner images.
"""

import sys

from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

from image_generation.temporal.constants import TemporalQueue
from image_generation.temporal.workflow import CollectionImageWorkflow
from image_generation.temporal.activities import (
    fetch_collection_data_activity,
    generate_collection_image_activity,
    save_collection_image_activity,
)
from config.settings import loaded_config
from utils.temporal.worker_registry import register_worker


@register_worker("collection_image_worker")
async def collection_image_worker():
    """
    Run the collection image generation Temporal worker.
    """
    try:
        print("COLLECTION_IMAGE_WORKER: Starting worker function...", file=sys.stderr, flush=True)

        temporal_host = loaded_config.temporal_host or "localhost:7233"
        temporal_namespace = loaded_config.temporal_namespace

        print(
            f"COLLECTION_IMAGE_WORKER: Connecting to Temporal at {temporal_host}...",
            file=sys.stderr,
            flush=True,
        )

        client = await Client.connect(
            target_host=temporal_host,
            namespace=temporal_namespace,
        )
        print("COLLECTION_IMAGE_WORKER: Connected to Temporal.", file=sys.stderr, flush=True)

        print("COLLECTION_IMAGE_WORKER: Creating Worker...", file=sys.stderr, flush=True)

        worker = Worker(
            client,
            task_queue=TemporalQueue.COLLECTION_IMAGE_GENERATION.value,
            workflows=[CollectionImageWorkflow],
            activities=[
                fetch_collection_data_activity,
                generate_collection_image_activity,
                save_collection_image_activity,
            ],
            workflow_runner=SandboxedWorkflowRunner(
                restrictions=SandboxRestrictions.default.with_passthrough_all_modules()
            ),
        )

        print("COLLECTION_IMAGE_WORKER: Worker created.", file=sys.stderr, flush=True)
        print(
            f"COLLECTION_IMAGE_WORKER: Listening on queue: {TemporalQueue.COLLECTION_IMAGE_GENERATION.value}",
            file=sys.stderr,
            flush=True,
        )

        await worker.run()

    except Exception as e:
        import traceback

        print(
            f"COLLECTION_IMAGE_WORKER: ERROR - {type(e).__name__}: {e}",
            file=sys.stderr,
            flush=True,
        )
        print("COLLECTION_IMAGE_WORKER: Full traceback:", file=sys.stderr, flush=True)
        traceback.print_exc()
        raise
