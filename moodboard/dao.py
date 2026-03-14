"""
ThemeMoodboard Data Access Object.

Provides database operations for the ThemeMoodboard model.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from collection_dna.moodboard.models import ThemeMoodboard
from utils.dao import BaseDAO


class ThemeMoodboardDAO(BaseDAO):
    """Data Access Object for ThemeMoodboard model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, db_model=ThemeMoodboard)

    async def create_moodboard(
        self,
        theme_id: UUID,
        status: str = "pending",
    ) -> ThemeMoodboard:
        """Create a new moodboard record for a theme."""
        moodboard = ThemeMoodboard(
            theme_id=theme_id,
            status=status,
        )
        self.session.add(moodboard)
        await self.session.flush()
        return moodboard

    async def select_by_id(self, moodboard_id: UUID) -> Optional[ThemeMoodboard]:
        """Get moodboard by ID."""
        query = select(ThemeMoodboard).where(ThemeMoodboard.id == moodboard_id)
        result = await self._execute_query(query)
        return result.scalar_one_or_none()

    async def select_by_theme_id(self, theme_id: UUID) -> Optional[ThemeMoodboard]:
        """Get moodboard by theme ID (one-to-one relationship)."""
        query = select(ThemeMoodboard).where(ThemeMoodboard.theme_id == theme_id)
        result = await self._execute_query(query)
        return result.scalar_one_or_none()

    async def update_collage_data(
        self,
        moodboard_id: UUID,
        moodboard_slug: str,
        collage_prompt: str,
        collage_reference_images: list[str],
    ) -> None:
        """Update moodboard with collage generation data."""
        query = (
            update(ThemeMoodboard)
            .where(ThemeMoodboard.id == moodboard_id)
            .values(
                moodboard_slug=moodboard_slug,
                collage_prompt=collage_prompt,
                collage_reference_images=collage_reference_images,
                status="generating_elements",
            )
        )
        await self._execute_query(query)

    async def update_element_prompts(
        self,
        moodboard_id: UUID,
        element_prompts: list[str],
    ) -> None:
        """Update moodboard with element prompts."""
        query = (
            update(ThemeMoodboard)
            .where(ThemeMoodboard.id == moodboard_id)
            .values(element_prompts=element_prompts)
        )
        await self._execute_query(query)

    async def update_collage_image_url(
        self,
        moodboard_id: UUID,
        collage_image_url: str,
    ) -> None:
        """Update moodboard with generated collage image URL."""
        query = (
            update(ThemeMoodboard)
            .where(ThemeMoodboard.id == moodboard_id)
            .values(collage_image_url=collage_image_url)
        )
        await self._execute_query(query)

    async def update_element_image_urls(
        self,
        moodboard_id: UUID,
        element_image_urls: list[str],
    ) -> None:
        """Update moodboard with generated element image URLs."""
        query = (
            update(ThemeMoodboard)
            .where(ThemeMoodboard.id == moodboard_id)
            .values(element_image_urls=element_image_urls)
        )
        await self._execute_query(query)

    async def update_status(self, moodboard_id: UUID, status: str) -> None:
        """Update moodboard status."""
        query = (
            update(ThemeMoodboard)
            .where(ThemeMoodboard.id == moodboard_id)
            .values(status=status)
        )
        await self._execute_query(query)

    async def update_status_by_theme_id(self, theme_id: UUID, status: str) -> None:
        """Update moodboard status by theme ID."""
        query = (
            update(ThemeMoodboard)
            .where(ThemeMoodboard.theme_id == theme_id)
            .values(status=status)
        )
        await self._execute_query(query)
