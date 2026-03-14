"""
Moodboard Generation Temporal Workflow.

Sequential workflow:
1. Create moodboard record (pending)
2. Generate collage prompt with web search
3. Split collage into element prompts
4. Mark as completed

Image generation is handled by a separate workflow.
"""

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from collection_dna.moodboard.temporal.constants import TemporalQueue

with workflow.unsafe.imports_passed_through():
    from collection_dna.moodboard.temporal.activities import (
        create_moodboard_record_activity,
        generate_collage_prompt_activity,
        split_into_elements_activity,
        mark_moodboard_completed_activity,
        mark_moodboard_failed_activity,
    )


@workflow.defn
class MoodboardGenerationWorkflow:
    """
    Temporal workflow for moodboard generation.

    Generates collage description and element prompts for a theme.
    Image generation is handled separately.

    Status transitions:
    - pending -> generating_collage -> generating_elements -> completed
    - Any state -> failed (on error)
    """

    @workflow.run
    async def run(self, event_data: dict[str, Any]) -> dict[str, Any]:
        theme_id = event_data.get("theme_id")
        theme_data = event_data.get("theme_data", {})
        brand_dna = event_data.get("brand_dna", {})

        workflow.logger.info(
            f"Starting moodboard generation for theme_id={theme_id}"
        )

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        results = {
            "theme_id": theme_id,
            "moodboard_id": None,
            "success": False,
            "error": None,
        }

        moodboard_id = None

        try:
            # =================================================================
            # Step 1: Create Moodboard Record
            # =================================================================
            workflow.logger.info("Step 1: Creating moodboard record...")

            create_result = await workflow.execute_activity(
                create_moodboard_record_activity,
                arg={"theme_id": theme_id},
                task_queue=TemporalQueue.MOODBOARD_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )

            moodboard_id = create_result["moodboard_id"]
            results["moodboard_id"] = moodboard_id

            workflow.logger.info(f"Created moodboard record: {moodboard_id}")

            # =================================================================
            # Step 2: Generate Collage Prompt
            # =================================================================
            workflow.logger.info("Step 2: Generating collage prompt...")

            collage_result = await workflow.execute_activity(
                generate_collage_prompt_activity,
                arg={
                    "moodboard_id": moodboard_id,
                    "theme_id": theme_id,
                    "theme_data": theme_data,
                    "brand_dna": brand_dna,
                    "brand_special_requests": event_data.get("brand_special_requests", ""),
                    "target_categories": event_data.get("target_categories", []),
                    "brand_category_details": event_data.get("brand_category_details", {}),
                    "competitors_string": event_data.get("competitors_string", ""),
                },
                task_queue=TemporalQueue.MOODBOARD_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=retry_policy,
            )

            moodboard_slug = collage_result["moodboard_slug"]
            collage_prompt = collage_result["collage_prompt"]

            workflow.logger.info(
                f"Generated collage prompt for moodboard_slug={moodboard_slug}"
            )

            # =================================================================
            # Step 3: Split into Elements
            # =================================================================
            workflow.logger.info("Step 3: Splitting into elements...")

            elements_result = await workflow.execute_activity(
                split_into_elements_activity,
                arg={
                    "moodboard_id": moodboard_id,
                    "moodboard_slug": moodboard_slug,
                    "collage_prompt": collage_prompt,
                },
                task_queue=TemporalQueue.MOODBOARD_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )

            element_count = elements_result["element_count"]

            workflow.logger.info(
                f"Split moodboard into {element_count} elements"
            )

            # =================================================================
            # Step 4: Mark as Completed
            # =================================================================
            workflow.logger.info("Step 4: Marking as completed...")

            await workflow.execute_activity(
                mark_moodboard_completed_activity,
                arg={"moodboard_id": moodboard_id},
                task_queue=TemporalQueue.MOODBOARD_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )

            results["success"] = True
            results["moodboard_slug"] = moodboard_slug
            results["element_count"] = element_count

            workflow.logger.info(
                f"Moodboard generation completed for theme_id={theme_id}"
            )

        except Exception as e:
            workflow.logger.error(
                f"Moodboard generation failed for theme_id={theme_id}: {e}"
            )

            # Mark as failed
            fail_params = {}
            if moodboard_id:
                fail_params["moodboard_id"] = moodboard_id
            else:
                fail_params["theme_id"] = theme_id

            await workflow.execute_activity(
                mark_moodboard_failed_activity,
                arg=fail_params,
                task_queue=TemporalQueue.MOODBOARD_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=2),
            )

            results["error"] = str(e)

        return results
