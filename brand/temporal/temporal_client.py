from datetime import timedelta
from typing import Any

from brand.temporal.constants import TemporalQueue
from brand.temporal.workflow import BrandOnboardingWorkflow
from utils.temporal.temporal_client import TemporalClient


class BrandOnboardingTemporalClient(TemporalClient):
    """Temporal client for brand onboarding workflows."""

    async def start_brand_onboarding_workflow(
        self,
        brand_id: str,
        user_request: dict[str, Any],
    ) -> str:
        """Start brand onboarding workflow."""
        workflow_id = await self.start_workflow(
            workflow_class=BrandOnboardingWorkflow,
            workflow_method=BrandOnboardingWorkflow.run,
            args=[{"brand_id": brand_id, "user_request": user_request}],
            workflow_id=f"brand-onboarding-{brand_id}",
            task_queue=TemporalQueue.BRAND_ONBOARDING.value,
            execution_timeout=timedelta(hours=2),
        )
        return workflow_id
