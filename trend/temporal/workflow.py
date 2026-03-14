"""
Theme Trend Temporal Workflow.

Fire-and-forget workflow for running category_trends and trend_spotting.
Sequential execution: category_trends → trend_spotting
"""

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from trend.temporal.constants import TemporalQueue

with workflow.unsafe.imports_passed_through():
    from trend.temporal.activities.trend_activities import (
        create_theme_trend_record_activity,
        run_category_trends_activity,
        run_trend_spotting_activity,
        mark_trend_failed_activity,
    )


@workflow.defn
class ThemeTrendWorkflow:
    """
    Temporal workflow for trend analysis.

    Fire-and-forget pattern: Parent workflow doesn't wait for completion.
    Sequential execution: category_trends → trend_spotting

    Status transitions:
    - pending → category_trends_done → completed
    - pending/category_trends_done → failed (on error)
    """

    @workflow.run
    async def run(self, event_data: dict[str, Any]) -> dict[str, Any]:
        theme_id = event_data.get("theme_id")
        theme_data = event_data.get("theme_data", {})
        brand_dna = event_data.get("brand_dna", {})

        workflow.logger.info(
            f"Starting theme trend workflow for theme_id={theme_id}"
        )

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=10),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        results = {
            "theme_id": theme_id,
            "category_trends_success": False,
            "trend_spotting_success": False,
            "error": None,
        }

        try:
            # =================================================================
            # Step 0: Create ThemeTrend record
            # =================================================================
            workflow.logger.info("Creating theme trend record...")

            await workflow.execute_activity(
                create_theme_trend_record_activity,
                arg={"theme_id": theme_id},
                task_queue=TemporalQueue.THEME_TREND.value,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )

            # =================================================================
            # Step 1: Run category_trends (sequential)
            # =================================================================
            workflow.logger.info("Running category_trends activity...")

            category_params = {
                "theme_id": theme_id,
                "theme_data": theme_data,
                "brand_dna": brand_dna,
                "brand_special_requests": event_data.get("brand_special_requests", ""),
                "target_categories": event_data.get("target_categories", []),
                "brand_category_details": event_data.get("brand_category_details", {}),
                "target_region": event_data.get("target_region", ""),
                "target_age": event_data.get("target_age", ""),
                "target_gender": event_data.get("target_gender", ""),
                "brand_classification": event_data.get("brand_classification", {}),
            }

            category_result = await workflow.execute_activity(
                run_category_trends_activity,
                arg=category_params,
                task_queue=TemporalQueue.THEME_TREND.value,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=retry_policy,
            )

            results["category_trends_success"] = category_result.get("success", False)
            workflow.logger.info(
                f"Category trends completed: {len(category_result.get('categories', []))} categories"
            )

            # =================================================================
            # Step 2: Run trend_spotting (sequential after category_trends)
            # =================================================================
            workflow.logger.info("Running trend_spotting activity...")

            trend_params = {
                "theme_id": theme_id,
                "themes_string": event_data.get("themes_string", ""),
                "brand_dna": brand_dna,
                "target_categories": event_data.get("target_categories", []),
            }

            trend_result = await workflow.execute_activity(
                run_trend_spotting_activity,
                arg=trend_params,
                task_queue=TemporalQueue.THEME_TREND.value,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=retry_policy,
            )

            results["trend_spotting_success"] = trend_result.get("success", False)
            workflow.logger.info("Trend spotting completed")

            workflow.logger.info(
                f"Theme trend workflow completed for theme_id={theme_id}"
            )

        except Exception as e:
            workflow.logger.error(
                f"Theme trend workflow failed for theme_id={theme_id}: {e}"
            )

            # Mark as failed
            await workflow.execute_activity(
                mark_trend_failed_activity,
                arg={"theme_id": theme_id},
                task_queue=TemporalQueue.THEME_TREND.value,
                start_to_close_timeout=timedelta(minutes=2),
            )

            results["error"] = str(e)

        return results
