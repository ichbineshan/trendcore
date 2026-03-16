"""
Style Generation Temporal Client.

Provides methods to start style generation workflows.
"""

import uuid
from datetime import timedelta
from typing import Any

from styles.temporal.constants import TemporalQueue
from styles.temporal.workflow import StyleGenerationWorkflow
from utils.temporal.temporal_client import TemporalClient


class StyleTemporalClient(TemporalClient):
    """Temporal client for style generation workflows."""

    async def start_style_generation_workflow(
        self,
        theme_id: str,
    ) -> str:
        """
        Start style generation workflow.

        Args:
            theme_id: UUID string of the theme

        Returns:
            Workflow ID
        """
        workflow_id = await self.start_workflow(
            workflow_class=StyleGenerationWorkflow,
            workflow_method=StyleGenerationWorkflow.run,
            args=[{
                "theme_id": theme_id,
            }],
            workflow_id=f"style-generation-{theme_id}-{uuid.uuid4()}",
            task_queue=TemporalQueue.STYLE_GENERATION.value,
            execution_timeout=timedelta(hours=1),
        )
        return workflow_id
