from uuid import UUID

import uuid6

from brand.dao import BrandDAO
from brand.models import Brand
from config.logging import logger
from utils.connection_handler import get_connection_handler_for_app


class BrandService:
    """Service layer for Brand operations."""

    @staticmethod
    async def create_brand(
        brand_name: str,
        user_request: dict,
    ) -> UUID:
        """Create a new brand record with pending status."""
        brand_id = uuid6.uuid7()

        async with get_connection_handler_for_app() as connection_handler:
            dao = BrandDAO(connection_handler.session)
            await dao.create_brand(
                brand_id=brand_id,
                brand_name=brand_name,
                user_request=user_request,
                status="pending",
            )
            await connection_handler.session.commit()
            logger.info(f"Created new brand: {brand_id}")

        return brand_id

    @staticmethod
    async def get_brand_by_id(brand_id: UUID) -> Brand | None:
        """Get brand by ID."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = BrandDAO(connection_handler.session)
            return await dao.select_by_id(brand_id)

    @staticmethod
    async def update_brand_status(brand_id: UUID, status: str) -> None:
        """Update brand status."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = BrandDAO(connection_handler.session)
            await dao.update_status(brand_id, status)
            await connection_handler.session.commit()

    @staticmethod
    async def update_brand_dna(
        brand_id: UUID,
        visual_identity: dict | None = None,
        design_guardrails: dict | None = None,
        market_positioning: dict | None = None,
        cultural_influences: dict | None = None,
        core_values_and_voice: dict | None = None,
        source_references: list[str] | None = None,
        brand_reference_images: list[dict] | None = None,
    ) -> None:
        """Update brand DNA fields."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = BrandDAO(connection_handler.session)
            await dao.update_brand_dna(
                brand_id=brand_id,
                visual_identity=visual_identity,
                design_guardrails=design_guardrails,
                market_positioning=market_positioning,
                cultural_influences=cultural_influences,
                core_values_and_voice=core_values_and_voice,
                source_references=source_references,
                brand_reference_images=brand_reference_images,
            )
            await connection_handler.session.commit()

    @staticmethod
    async def update_brand_classification(
        brand_id: UUID,
        velocity: float | None = None,
        depth: float | None = None,
        strictness: float | None = None,
        classification_notes: str | None = None,
        brand_class: str | None = None,
        classification_reasoning: str | None = None,
    ) -> None:
        """Update brand classification fields."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = BrandDAO(connection_handler.session)
            await dao.update_brand_classification(
                brand_id=brand_id,
                velocity=velocity,
                depth=depth,
                strictness=strictness,
                classification_notes=classification_notes,
                brand_class=brand_class,
                classification_reasoning=classification_reasoning,
            )
            await connection_handler.session.commit()
