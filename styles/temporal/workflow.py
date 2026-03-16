"""
Style Generation Temporal Workflow.

Triggers style generation via Naruto API for a theme.
"""

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from styles.temporal.constants import TemporalQueue

with workflow.unsafe.imports_passed_through():
    from styles.temporal.activities import (
        trigger_style_generation_activity,
        mark_style_failed_activity,
    )


@workflow.defn
class StyleGenerationWorkflow:
    """
    Temporal workflow for style generation.

    Triggers Naruto API and waits for webhook callback.
    """

    @workflow.run
    async def run(self, event_data: dict[str, Any]) -> dict[str, Any]:
        theme_id = event_data.get("theme_id")

        workflow.logger.info(f"Starting style generation for theme_id={theme_id}")

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        results = {
            "theme_id": theme_id,
            "style_id": None,
            "success": False,
            "error": None,
        }

        try:
            result = await workflow.execute_activity(
                trigger_style_generation_activity,
                arg={"theme_id": theme_id},
                task_queue=TemporalQueue.STYLE_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )

            results["style_id"] = result.get("style_id")
            results["success"] = result.get("success", False)

            workflow.logger.info(
                f"Style generation triggered for theme_id={theme_id}, "
                f"style_id={results['style_id']}"
            )

        except Exception as e:
            workflow.logger.error(
                f"Style generation failed for theme_id={theme_id}: {e}"
            )

            # If we got a style_id before failure, mark it as failed
            if results.get("style_id"):
                await workflow.execute_activity(
                    mark_style_failed_activity,
                    arg={"style_id": results["style_id"], "error": str(e)},
                    task_queue=TemporalQueue.STYLE_GENERATION.value,
                    start_to_close_timeout=timedelta(minutes=2),
                )

            results["error"] = str(e)

        return results
