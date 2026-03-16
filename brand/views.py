import logging
from typing import Any

from brand.schemas import BrandOnboardingRequest, BrandOnboardingResponse
from brand.service import BrandService
from brand.temporal.temporal_client import BrandOnboardingTemporalClient

logger = logging.getLogger(__name__)


async def onboard_brand(
    request: BrandOnboardingRequest,
) -> dict[str, Any]:
    """
    Onboard a new brand.

    1. Extract brand_name from payload
    2. Store entire payload in user_request
    3. Trigger Temporal workflow
    4. Return brand_id with pending status
    """
    try:
        user_request = request.model_dump()
        brand_name = request.brand_name

        brand_id = await BrandService.create_brand(
            brand_name=brand_name,
            user_request=user_request,
        )

        temporal_client = BrandOnboardingTemporalClient()
        workflow_id = await temporal_client.start_brand_onboarding_workflow(
            brand_id=str(brand_id),
            user_request=user_request,
        )

        logger.info(
            f"Brand onboarding started",
            extra={"brand_id": str(brand_id), "workflow_id": workflow_id}
        )

        return BrandOnboardingResponse(
            success=True,
            message="Brand onboarding started",
            data={
                "brand_id": str(brand_id),
                "status": "pending",
                "workflow_id": workflow_id,
            },
        ).model_dump()

    except Exception as e:
        logger.exception(f"Failed to onboard brand: {e}")
        return BrandOnboardingResponse(
            success=False,
            message="Failed to onboard brand",
            error=str(e),
        ).model_dump()
