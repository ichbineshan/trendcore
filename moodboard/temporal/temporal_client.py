"""
Moodboard Generation Temporal Client.

Provides methods to start moodboard generation workflows.
"""

import uuid
from datetime import timedelta
from typing import Any

from collection_dna.moodboard.temporal.constants import TemporalQueue
from collection_dna.moodboard.temporal.workflow import MoodboardGenerationWorkflow
from utils.temporal.temporal_client import TemporalClient


class MoodboardTemporalClient(TemporalClient):
    """Temporal client for moodboard generation workflows."""

    async def start_moodboard_generation_workflow(
        self,
        theme_id: str,
        theme_data: dict[str, Any],
        brand_dna: dict[str, Any],
        brand_special_requests: str = "",
        target_categories: list[str] | None = None,
        brand_category_details: dict[str, Any] | None = None,
        competitors_string: str = "",
    ) -> str:
        """Start moodboard generation workflow for a theme."""
        workflow_id = await self.start_workflow(
            workflow_class=MoodboardGenerationWorkflow,
            workflow_method=MoodboardGenerationWorkflow.run,
            args=[{
                "theme_id": theme_id,
                "theme_data": theme_data,
                "brand_dna": brand_dna,
                "brand_special_requests": brand_special_requests,
                "target_categories": target_categories or [],
                "brand_category_details": brand_category_details or {},
                "competitors_string": competitors_string,
            }],
            workflow_id=f"moodboard-generation-{theme_id}-{uuid.uuid4()}",
            task_queue=TemporalQueue.MOODBOARD_GENERATION.value,
            execution_timeout=timedelta(hours=1),
        )
        return workflow_id
