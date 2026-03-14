from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from brand.models import Brand
from utils.dao import BaseDAO


class BrandDAO(BaseDAO):
    """Data Access Object for Brand model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, db_model=Brand)

    async def create_brand(
        self,
        brand_id: UUID,
        brand_name: str,
        user_request: dict,
        status: str = "pending",
    ) -> Brand:
        """Create a new brand record."""
        brand = Brand(
            id=brand_id,
            brand_name=brand_name,
            status=status,
            user_request=user_request,
        )
        self.session.add(brand)
        return brand

    async def select_by_id(self, brand_id: UUID) -> Optional[Brand]:
        """Select brand by ID."""
        query = select(Brand).where(Brand.id == brand_id)
        result = await self._execute_query(query)
        return result.scalar_one_or_none()

    async def update_status(self, brand_id: UUID, status: str) -> None:
        """Update brand status."""
        query = (
            update(Brand)
            .where(Brand.id == brand_id)
            .values(status=status)
        )
        await self._execute_query(query)

    async def update_brand_dna(
        self,
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
        update_values = {}
        if visual_identity is not None:
            update_values["visual_identity"] = visual_identity
        if design_guardrails is not None:
            update_values["design_guardrails"] = design_guardrails
        if market_positioning is not None:
            update_values["market_positioning"] = market_positioning
        if cultural_influences is not None:
            update_values["cultural_influences"] = cultural_influences
        if core_values_and_voice is not None:
            update_values["core_values_and_voice"] = core_values_and_voice
        if source_references is not None:
            update_values["source_references"] = source_references
        if brand_reference_images is not None:
            update_values["brand_reference_images"] = brand_reference_images

        if update_values:
            query = (
                update(Brand)
                .where(Brand.id == brand_id)
                .values(**update_values)
            )
            await self._execute_query(query)

    async def update_brand_classification(
        self,
        brand_id: UUID,
        velocity: float | None = None,
        depth: float | None = None,
        strictness: float | None = None,
        classification_notes: str | None = None,
        brand_class: str | None = None,
        classification_reasoning: str | None = None,
    ) -> None:
        """Update brand classification fields."""
        update_values = {}
        if velocity is not None:
            update_values["velocity"] = velocity
        if depth is not None:
            update_values["depth"] = depth
        if strictness is not None:
            update_values["strictness"] = strictness
        if classification_notes is not None:
            update_values["classification_notes"] = classification_notes
        if brand_class is not None:
            update_values["brand_class"] = brand_class
        if classification_reasoning is not None:
            update_values["classification_reasoning"] = classification_reasoning

        if update_values:
            query = (
                update(Brand)
                .where(Brand.id == brand_id)
                .values(**update_values)
            )
            await self._execute_query(query)
