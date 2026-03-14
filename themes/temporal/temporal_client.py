"""
Theme Generation Temporal Client.

Provides methods to start theme generation workflows.
"""

import uuid
from datetime import timedelta
from typing import Any

from themes.temporal.constants import TemporalQueue
from themes.temporal.workflow import ThemeGenerationWorkflow
from utils.temporal.temporal_client import TemporalClient


class ThemeTemporalClient(TemporalClient):
    """Temporal client for theme generation workflows."""

    async def start_theme_generation_workflow(
        self,
        collection_id: str,
        user_req: dict[str, Any],
        brand_dna: dict[str, Any],
        theme_ids: list[str],
    ) -> str:
        """Start theme generation workflow."""
        workflow_id = await self.start_workflow(
            workflow_class=ThemeGenerationWorkflow,
            workflow_method=ThemeGenerationWorkflow.run,
            args=[{
                "collection_id": collection_id,
                "user_req": user_req,
                "brand_dna": brand_dna,
                "theme_ids": theme_ids,
            }],
            workflow_id=f"theme-generation-{collection_id}-{uuid.uuid4()}",
            task_queue=TemporalQueue.THEME_GENERATION.value,
            execution_timeout=timedelta(hours=1),
        )
        return workflow_id
