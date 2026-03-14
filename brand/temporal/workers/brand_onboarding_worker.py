"""
Brand Onboarding Temporal Worker.
"""

import logging

from temporalio.client import Client
from temporalio.worker import Worker

from brand.temporal.constants import TemporalQueue
from brand.temporal.workflow import BrandOnboardingWorkflow
from brand.temporal.activities import (
    brand_category_activity,
    brand_dna_activity,
    brand_classification_activity,
    update_brand_completed_activity,
    update_brand_failed_activity,
)
from config.settings import loaded_config
from utils.temporal.worker_registry import register_worker

logger = logging.getLogger(__name__)

@register_worker("brand_onboarding_worker")
async def brand_onboarding_worker():
    """Run the brand onboarding Temporal worker."""
    client = await Client.connect(loaded_config.temporal_host)

    worker = Worker(
        client,
        task_queue=TemporalQueue.BRAND_ONBOARDING.value,
        workflows=[BrandOnboardingWorkflow],
        activities=[
            brand_category_activity,
            brand_dna_activity,
            brand_classification_activity,
            update_brand_completed_activity,
            update_brand_failed_activity,
        ],
    )

    logger.info(f"Starting brand onboarding worker on queue: {TemporalQueue.BRAND_ONBOARDING.value}")
    await worker.run()


