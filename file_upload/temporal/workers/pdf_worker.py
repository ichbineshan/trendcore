"""Worker for PDF processing workflows."""
import sys

from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

from config.settings import loaded_config
from file_upload.temporal.activities import (
    extract_pdf_chunks_activity,
    index_pdf_chunk_activity,
)
from file_upload.temporal.constants import TemporalQueue
from file_upload.temporal.workflow import PDFProcessingWorkflow
from utils.temporal.worker_registry import register_worker


@register_worker("pdf_processing_worker")
async def pdf_processing_worker():
    """Run the PDF processing worker."""
    try:
        temporal_host = loaded_config.temporal_host or "localhost:7233"
        temporal_namespace = loaded_config.temporal_namespace

        client = await Client.connect(
            target_host=temporal_host,
            namespace=temporal_namespace
        )

        print(f"TEMPORAL_WORKER: Connected to Temporal server successfully", file=sys.stderr, flush=True)
        print(f"TEMPORAL_WORKER: Creating worker...", file=sys.stderr, flush=True)

        worker = Worker(
            client,
            task_queue=TemporalQueue.PDF_PROCESSING.value,
            workflows=[PDFProcessingWorkflow],
            activities=[
                extract_pdf_chunks_activity,
                index_pdf_chunk_activity,
            ],
            max_concurrent_activities=loaded_config.temporal_max_concurrent_activities,
            workflow_runner=SandboxedWorkflowRunner(
                restrictions=SandboxRestrictions.default.with_passthrough_all_modules()
            )
        )

        print("TEMPORAL_WORKER: Starting worker (this will block)...", file=sys.stderr, flush=True)

        await worker.run()

    except Exception:
        raise
