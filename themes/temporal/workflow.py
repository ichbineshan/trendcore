"""
Theme Generation Temporal Workflow.

Two-Phase approach:
- Phase 1: Generate distinct theme briefs (sequential)
- Phase 2: Expand each brief into full theme (parallel)
- Fire-and-forget: Start trend workflows for each successful theme
"""

import asyncio
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.workflow import ParentClosePolicy

from themes.temporal.constants import TemporalQueue

with workflow.unsafe.imports_passed_through():
    from themes.temporal.activities import (
        generate_theme_briefs_activity,
        generate_single_theme_activity,
        update_themes_completed_activity,
        update_themes_failed_activity,
    )
    from trend.temporal.workflow import ThemeTrendWorkflow
    from trend.temporal.constants import TemporalQueue as TrendQueue


@workflow.defn
class ThemeGenerationWorkflow:
    """
    Temporal workflow for two-phase theme generation.

    Phase 1: Single activity generates distinct theme briefs
    Phase 2: Parallel activities expand each brief into full theme
    """

    @workflow.run
    async def run(self, event_data: dict[str, Any]) -> dict[str, Any]:
        collection_id = event_data.get("collection_id")
        user_req = event_data.get("user_req", {})
        brand_dna = event_data.get("brand_dna", {})
        theme_ids = event_data.get("theme_ids", [])

        workflow.logger.info(
            f"Starting two-phase theme generation for collection_id={collection_id}, "
            f"theme_count={len(theme_ids)}"
        )

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        results = {
            "collection_id": collection_id,
            "phase1_success": False,
            "phase2_results": [],
            "successful_themes": [],
            "failed_themes": [],
        }

        try:
            # =================================================================
            # Phase 1: Generate Distinct Theme Briefs (Sequential)
            # =================================================================
            workflow.logger.info("Phase 1: Generating theme briefs...")

            state = {
                "collection_id": collection_id,
                "user_req": user_req,
                "brand_dna": brand_dna,
                "theme_ids": theme_ids,
            }

            state = await workflow.execute_activity(
                generate_theme_briefs_activity,
                arg=state,
                task_queue=TemporalQueue.THEME_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )

            briefs = state.get("briefs", [])
            results["phase1_success"] = True

            workflow.logger.info(
                f"Phase 1 completed: {len(briefs)} briefs generated. "
                f"Rationale: {state.get('distinctiveness_rationale', 'N/A')[:100]}..."
            )

            # =================================================================
            # Phase 2: Generate Full Theme Details (Parallel)
            # =================================================================
            workflow.logger.info(f"Phase 2: Generating {len(briefs)} themes in parallel...")

            # Prepare activity params for each theme
            phase2_tasks = []
            for brief_data in briefs:
                params = {
                    "theme_id": brief_data["theme_id"],
                    "brief": brief_data["brief"],
                    "user_req": user_req,
                    "brand_dna": brand_dna,
                    "collection_id": collection_id,
                }

                # Create activity execution (don't await yet)
                task = workflow.execute_activity(
                    generate_single_theme_activity,
                    arg=params,
                    task_queue=TemporalQueue.THEME_GENERATION.value,
                    start_to_close_timeout=timedelta(minutes=20),
                    retry_policy=retry_policy,
                )
                phase2_tasks.append(task)

            # Execute all Phase 2 activities in parallel
            phase2_results = await asyncio.gather(*phase2_tasks, return_exceptions=True)

            # Process results
            for idx, result in enumerate(phase2_results):
                if isinstance(result, Exception):
                    # Activity raised exception
                    theme_id = briefs[idx]["theme_id"] if idx < len(briefs) else "unknown"
                    workflow.logger.error(f"Theme {theme_id} failed with exception: {result}")
                    results["failed_themes"].append({
                        "theme_id": str(theme_id),
                        "error": str(result),
                    })
                elif isinstance(result, dict):
                    if result.get("success"):
                        results["successful_themes"].append(result)
                    else:
                        results["failed_themes"].append(result)

            results["phase2_results"] = [
                r if isinstance(r, dict) else {"error": str(r)}
                for r in phase2_results
            ]

            workflow.logger.info(
                f"Phase 2 completed: {len(results['successful_themes'])} succeeded, "
                f"{len(results['failed_themes'])} failed"
            )

            # =================================================================
            # Mark successful themes as completed
            # =================================================================
            if results["successful_themes"]:
                successful_ids = [t["theme_id"] for t in results["successful_themes"]]
                await workflow.execute_activity(
                    update_themes_completed_activity,
                    arg={
                        "collection_id": collection_id,
                        "theme_ids": successful_ids,
                    },
                    task_queue=TemporalQueue.THEME_GENERATION.value,
                    start_to_close_timeout=timedelta(minutes=5),
                )

            # =================================================================
            # Fire-and-Forget: Start trend workflows for each successful theme
            # =================================================================
            if results["successful_themes"]:
                workflow.logger.info(
                    f"Starting fire-and-forget trend workflows for "
                    f"{len(results['successful_themes'])} themes..."
                )

                for theme_result in results["successful_themes"]:
                    theme_id = theme_result["theme_id"]
                    theme_name = theme_result.get("theme_name", "unknown")

                    # Find the corresponding brief for this theme
                    theme_brief = None
                    for brief_data in briefs:
                        if brief_data["theme_id"] == theme_id:
                            theme_brief = brief_data["brief"]
                            break

                    # Build theme data for trend workflow
                    theme_data = {
                        "theme_name": theme_name,
                        "theme_slug": theme_brief.get("theme_slug", "") if theme_brief else "",
                        "core_concept": theme_brief.get("core_concept", "") if theme_brief else "",
                    }

                    # Build themes_string for trend_spotting
                    themes_string = f"Theme: {theme_name}\nConcept: {theme_data.get('core_concept', '')}"

                    trend_event_data = {
                        "theme_id": theme_id,
                        "theme_data": theme_data,
                        "brand_dna": brand_dna,
                        "themes_string": themes_string,
                        "brand_special_requests": user_req.get("brand_special_requests", ""),
                        "target_categories": user_req.get("categories", []),
                        "brand_category_details": user_req.get("brand_category_details", {}),
                        "target_region": user_req.get("region", ""),
                        "target_age": user_req.get("target_age", ""),
                        "target_gender": user_req.get("target_gender", ""),
                        "brand_classification": brand_dna.get("brand_classification", {}),
                    }

                    # Start child workflow with ABANDON policy (fire-and-forget)
                    await workflow.start_child_workflow(
                        ThemeTrendWorkflow.run,
                        trend_event_data,
                        id=f"theme-trend-{theme_id}",
                        task_queue=TrendQueue.THEME_TREND.value,
                        parent_close_policy=ParentClosePolicy.ABANDON,
                        execution_timeout=timedelta(hours=2),
                    )

                    workflow.logger.info(
                        f"Started fire-and-forget trend workflow for theme: {theme_name}"
                    )

            workflow.logger.info(f"Theme generation workflow completed for {collection_id}")

        except Exception as e:
            workflow.logger.exception(
                f"Theme generation failed for collection_id={collection_id}: {e}"
            )

            # Mark all themes as failed
            await workflow.execute_activity(
                update_themes_failed_activity,
                arg={"collection_id": collection_id, "theme_ids": theme_ids},
                task_queue=TemporalQueue.THEME_GENERATION.value,
                start_to_close_timeout=timedelta(minutes=5),
            )

            results["error"] = str(e)

        return results
