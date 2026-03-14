"""
Theme Trend Temporal Client.

Provides methods to start trend workflows with fire-and-forget pattern.
"""

import uuid
from datetime import timedelta
from typing import Any

from temporalio.common import WorkflowIDConflictPolicy

from trend.temporal.constants import TemporalQueue
from trend.temporal.workflow import ThemeTrendWorkflow
from utils.temporal.temporal_client import TemporalClient


class ThemeTrendTemporalClient(TemporalClient):
    """Temporal client for theme trend workflows."""

    async def start_trend_workflow_fire_and_forget(
        self,
        theme_id: str,
        theme_data: dict[str, Any],
        brand_dna: dict[str, Any],
        themes_string: str = "",
        brand_special_requests: str = "",
        target_categories: list[str] | None = None,
        brand_category_details: dict[str, Any] | None = None,
        target_region: str = "",
        target_age: str = "",
        target_gender: str = "",
        brand_classification: dict[str, Any] | None = None,
    ) -> str:
        """
        Start a fire-and-forget trend workflow for a single theme.

        This workflow runs independently and doesn't block the parent.
        Uses ParentClosePolicy.ABANDON implicitly via fire-and-forget pattern.

        Args:
            theme_id: Theme UUID string
            theme_data: Theme details (name, slug, concepts, etc.)
            brand_dna: Brand DNA data
            themes_string: Serialized themes for trend_spotting
            brand_special_requests: Special brand requests
            target_categories: Target category list
            brand_category_details: Category details
            target_region: Target region
            target_age: Target age range
            target_gender: Target gender
            brand_classification: Brand classification data

        Returns:
            workflow_id: The started workflow ID
        """
        workflow_id = f"theme-trend-{theme_id}-{uuid.uuid4()}"

        event_data = {
            "theme_id": theme_id,
            "theme_data": theme_data,
            "brand_dna": brand_dna,
            "themes_string": themes_string,
            "brand_special_requests": brand_special_requests,
            "target_categories": target_categories or [],
            "brand_category_details": brand_category_details or {},
            "target_region": target_region,
            "target_age": target_age,
            "target_gender": target_gender,
            "brand_classification": brand_classification or {},
        }

        workflow_id = await self.start_workflow(
            workflow_class=ThemeTrendWorkflow,
            workflow_method=ThemeTrendWorkflow.run,
            args=[event_data],
            workflow_id=workflow_id,
            task_queue=TemporalQueue.THEME_TREND.value,
            execution_timeout=timedelta(hours=2),
        )

        return workflow_id
