"""
Collection Generation Temporal Workflow.

Orchestrates collection overview generation and future activities.
"""

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from collection.temporal.constants import TemporalQueue

with workflow.unsafe.imports_passed_through():
    from collection.temporal.activities import (
        generate_overview_activity,
        update_collection_completed_activity,
        update_collection_failed_activity,
    )


@workflow.defn
class CollectionGenerationWorkflow:
    """
    Temporal workflow for collection generation.

    Runs sequentially:
    1. generate_overview_activity - Generate collection name, overview, range_overview
    2. (Future activities can be added here)
    3. update_collection_completed_activity - Mark as completed
    """

    @workflow.run
    async def run(self, event_data: dict[str, Any]) -> str | None:
        collection_id = event_data.get("collection_id")
        user_req = event_data.get("user_req", {})

        workflow.logger.info(f"Starting collection generation workflow for collection_id={collection_id}")

        state = {
            "collection_id": collection_id,
            "user_req": user_req,
        }

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        try:
            # Activity 1: Generate Overview
            state = await workflow.execute_activity(
                generate_overview_activity,
                arg=state,
                task_queue=TemporalQueue.COLLECTION_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=retry_policy,
            )

            # Future activities can be added here

            # Final Activity: Update collection as completed
            await workflow.execute_activity(
                update_collection_completed_activity,
                arg=state,
                task_queue=TemporalQueue.COLLECTION_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )

            workflow.logger.info(f"Collection generation completed for collection_id={collection_id}")

        except Exception as e:
            workflow.logger.exception(f"Collection generation failed for collection_id={collection_id}: {e}")

            await workflow.execute_activity(
                update_collection_failed_activity,
                arg={"collection_id": collection_id},
                task_queue=TemporalQueue.COLLECTION_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=5),
            )

        return None
