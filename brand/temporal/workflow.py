"""
Brand Onboarding Temporal Workflow.

Orchestrates brand_category, brand_dna, and brand_classification activities.
"""

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from brand.temporal.constants import TemporalQueue

with workflow.unsafe.imports_passed_through():
    from brand.temporal.activities import (
        brand_category_activity,
        brand_dna_activity,
        brand_classification_activity,
        update_brand_completed_activity,
        update_brand_failed_activity,
    )


@workflow.defn
class BrandOnboardingWorkflow:
    """
    Temporal workflow for brand onboarding.

    Runs sequentially:
    1. brand_category_activity - Extract product categories
    2. brand_dna_activity - Extract brand DNA
    3. brand_classification_activity - Classify brand
    4. update_brand_completed_activity - Mark as completed
    """

    @workflow.run
    async def run(self, event_data: dict[str, Any]) -> str | None:
        brand_id = event_data.get("brand_id")
        user_request = event_data.get("user_request", {})

        workflow.logger.info(f"Starting brand onboarding workflow for brand_id={brand_id}")

        state = {
            "brand_id": brand_id,
            "user_request": user_request,
            "brand_dna": {},
            "brand_classification": {},
        }

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        try:
            # Activity 1: Brand Category
            state = await workflow.execute_activity(
                brand_category_activity,
                arg=state,
                task_queue=TemporalQueue.BRAND_ONBOARDING.value,
                start_to_close_timeout=timedelta(minutes=60),
                retry_policy=retry_policy,
            )

            # Activity 2: Brand DNA
            state = await workflow.execute_activity(
                brand_dna_activity,
                arg=state,
                task_queue=TemporalQueue.BRAND_ONBOARDING.value,
                start_to_close_timeout=timedelta(minutes=60),
                retry_policy=retry_policy,
            )

            # Activity 3: Brand Classification
            state = await workflow.execute_activity(
                brand_classification_activity,
                arg=state,
                task_queue=TemporalQueue.BRAND_ONBOARDING.value,
                start_to_close_timeout=timedelta(minutes=40),
                retry_policy=retry_policy,
            )

            # Activity 4: Update brand as completed
            await workflow.execute_activity(
                update_brand_completed_activity,
                arg=state,
                task_queue=TemporalQueue.BRAND_ONBOARDING.value,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )

            workflow.logger.info(f"Brand onboarding completed for brand_id={brand_id}")

        except Exception as e:
            workflow.logger.exception(f"Brand onboarding failed for brand_id={brand_id}: {e}")

            await workflow.execute_activity(
                update_brand_failed_activity,
                arg={"brand_id": brand_id},
                task_queue=TemporalQueue.BRAND_ONBOARDING.value,
                start_to_close_timeout=timedelta(minutes=5),
            )

        return None
