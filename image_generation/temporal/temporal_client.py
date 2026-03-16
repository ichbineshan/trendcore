import uuid
from datetime import timedelta

from image_generation.temporal.constants import TemporalQueue
from image_generation.temporal.workflow import CollectionImageWorkflow
from utils.temporal.temporal_client import TemporalClient


class ImageGenerationTemporalClient(TemporalClient):
    """Temporal client for image generation workflows."""

    async def start_collection_image_workflow(
        self,
        collection_id: str,
    ) -> str:
        """
        Start collection image generation workflow (fire-and-forget).

        Args:
            collection_id: UUID of the collection to generate image for.

        Returns:
            workflow_id: The ID of the started workflow.
        """
        workflow_id = await self.start_workflow(
            workflow_class=CollectionImageWorkflow,
            workflow_method=CollectionImageWorkflow.run,
            args=[{"collection_id": collection_id}],
            workflow_id=f"collection-image-{collection_id}-{uuid.uuid4()}",
            task_queue=TemporalQueue.COLLECTION_IMAGE_GENERATION.value,
            execution_timeout=timedelta(hours=1),
        )
        return workflow_id
