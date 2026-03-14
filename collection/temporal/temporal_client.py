import uuid
from datetime import timedelta
from typing import Any

from collection.temporal.constants import TemporalQueue
from collection.temporal.workflow import CollectionGenerationWorkflow
from utils.temporal.temporal_client import TemporalClient


class CollectionTemporalClient(TemporalClient):
    """Temporal client for collection generation workflows."""

    async def start_collection_generation_workflow(
        self,
        collection_id: str,
        user_req: dict[str, Any],
    ) -> str:
        """Start collection generation workflow."""
        workflow_id = await self.start_workflow(
            workflow_class=CollectionGenerationWorkflow,
            workflow_method=CollectionGenerationWorkflow.run,
            args=[{"collection_id": collection_id, "user_req": user_req}],
            workflow_id=f"collection-generation-{collection_id}-{uuid.uuid4()}",
            task_queue=TemporalQueue.COLLECTION_GENERATION.value,
            execution_timeout=timedelta(hours=1),
        )
        return workflow_id
