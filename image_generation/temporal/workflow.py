"""
Image Generation Temporal Workflows.

Workflows:
1. MoodboardImageWorkflow - Generates moodboard collage and element images
2. CollectionImageWorkflow - Generates collection hero/banner image
"""

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from image_generation.temporal.constants import TemporalQueue

with workflow.unsafe.imports_passed_through():
    from image_generation.temporal.activities import (
        fetch_moodboard_data_activity,
        generate_collage_image_activity,
        generate_element_images_activity,
        mark_images_completed_activity,
        mark_images_failed_activity,
        fetch_collection_data_activity,
        generate_collection_image_activity,
        save_collection_image_activity,
    )


@workflow.defn
class MoodboardImageWorkflow:
    """
    Temporal workflow for moodboard image generation.

    Generates collage and element images for a single moodboard
    using Vertex AI with rate limiting.

    Status transitions:
    - pending -> generating -> completed
    - generating -> failed (on error)
    """

    @workflow.run
    async def run(self, event_data: dict[str, Any]) -> dict[str, Any]:
        moodboard_id = event_data.get("moodboard_id")

        workflow.logger.info(f"Starting image generation for moodboard_id={moodboard_id}")

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        results = {
            "moodboard_id": moodboard_id,
            "success": False,
            "collage_image_url": None,
            "element_image_urls": [],
            "error": None,
        }

        try:
            # =================================================================
            # Step 1: Fetch Moodboard Data
            # =================================================================
            workflow.logger.info("Step 1: Fetching moodboard data...")

            moodboard_data = await workflow.execute_activity(
                fetch_moodboard_data_activity,
                arg={"moodboard_id": moodboard_id},
                task_queue=TemporalQueue.MOODBOARD_IMAGE_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )

            collage_prompt = moodboard_data.get("collage_prompt", "")
            element_prompts = moodboard_data.get("element_prompts", [])

            workflow.logger.info(
                f"Fetched data: collage_prompt length={len(collage_prompt)}, "
                f"element_prompts count={len(element_prompts)}"
            )

            # =================================================================
            # Step 2: Generate Collage Image
            # =================================================================
            workflow.logger.info("Step 2: Generating collage image...")

            collage_result = await workflow.execute_activity(
                generate_collage_image_activity,
                arg={
                    "moodboard_id": moodboard_id,
                    "collage_prompt": collage_prompt,
                },
                task_queue=TemporalQueue.MOODBOARD_IMAGE_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=retry_policy,
            )

            results["collage_image_url"] = collage_result.get("collage_image_url")

            workflow.logger.info(
                f"Collage image generated: {results['collage_image_url']}"
            )

            # =================================================================
            # Step 3: Generate Element Images
            # =================================================================
            workflow.logger.info(
                f"Step 3: Generating {len(element_prompts)} element images..."
            )

            elements_result = await workflow.execute_activity(
                generate_element_images_activity,
                arg={
                    "moodboard_id": moodboard_id,
                    "element_prompts": element_prompts,
                },
                task_queue=TemporalQueue.MOODBOARD_IMAGE_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=120),
                retry_policy=retry_policy,
            )

            results["element_image_urls"] = elements_result.get("element_image_urls", [])

            workflow.logger.info(
                f"Element images generated: {len(results['element_image_urls'])}"
            )

            # =================================================================
            # Step 4: Mark as Completed
            # =================================================================
            workflow.logger.info("Step 4: Marking as completed...")

            await workflow.execute_activity(
                mark_images_completed_activity,
                arg={"moodboard_id": moodboard_id},
                task_queue=TemporalQueue.MOODBOARD_IMAGE_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )

            results["success"] = True

            workflow.logger.info(
                f"Image generation completed for moodboard_id={moodboard_id}"
            )

        except Exception as e:
            workflow.logger.error(
                f"Image generation failed for moodboard_id={moodboard_id}: {e}"
            )

            # Mark as failed
            await workflow.execute_activity(
                mark_images_failed_activity,
                arg={"moodboard_id": moodboard_id},
                task_queue=TemporalQueue.MOODBOARD_IMAGE_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=2),
            )

            results["error"] = str(e)

        return results


@workflow.defn
class CollectionImageWorkflow:
    """
    Temporal workflow for collection hero image generation.

    Generates a single hero/banner image for a collection
    using collection_name and overview as prompt.

    Fire-and-forget: Does NOT update DB on failure.
    """

    @workflow.run
    async def run(self, event_data: dict[str, Any]) -> dict[str, Any]:
        collection_id = event_data.get("collection_id")

        workflow.logger.info(f"Starting image generation for collection_id={collection_id}")

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        results = {
            "collection_id": collection_id,
            "success": False,
            "image_url": None,
            "error": None,
        }

        try:
            # =================================================================
            # Step 1: Fetch Collection Data
            # =================================================================
            workflow.logger.info("Step 1: Fetching collection data...")

            collection_data = await workflow.execute_activity(
                fetch_collection_data_activity,
                arg={"collection_id": collection_id},
                task_queue=TemporalQueue.COLLECTION_IMAGE_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )

            collection_name = collection_data.get("collection_name", "")
            overview = collection_data.get("overview", "")

            workflow.logger.info(
                f"Fetched data: collection_name={collection_name[:50]}..."
            )

            # =================================================================
            # Step 2: Generate Hero Image
            # =================================================================
            workflow.logger.info("Step 2: Generating hero image...")

            image_result = await workflow.execute_activity(
                generate_collection_image_activity,
                arg={
                    "collection_id": collection_id,
                    "collection_name": collection_name,
                    "overview": overview,
                },
                task_queue=TemporalQueue.COLLECTION_IMAGE_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=retry_policy,
            )

            image_url = image_result.get("image_url")
            results["image_url"] = image_url

            workflow.logger.info(f"Hero image generated: {image_url}")

            # =================================================================
            # Step 3: Save Image URL (only on success)
            # =================================================================
            if image_url:
                workflow.logger.info("Step 3: Saving image URL...")

                await workflow.execute_activity(
                    save_collection_image_activity,
                    arg={
                        "collection_id": collection_id,
                        "image_url": image_url,
                    },
                    task_queue=TemporalQueue.COLLECTION_IMAGE_GENERATION.value,
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=retry_policy,
                )

                workflow.logger.info(f"Image URL saved for collection: {collection_id}")

            results["success"] = True

            workflow.logger.info(
                f"Image generation completed for collection_id={collection_id}"
            )

        except Exception as e:
            workflow.logger.error(
                f"Image generation failed for collection_id={collection_id}: {e}"
            )
            # Fire-and-forget: Do NOT update DB on failure
            results["error"] = str(e)

        return results
