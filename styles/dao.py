"""
Style Data Access Object.

Provides database operations for the ThemeStyle model.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from styles.models import ThemeStyle
from utils.dao import BaseDAO


class StyleDAO(BaseDAO):
    """Data Access Object for ThemeStyle model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, db_model=ThemeStyle)

    async def create_style(
        self,
        theme_id: UUID,
        external_job_id: Optional[str] = None,
        external_style_id: Optional[str] = None,
        status: str = "pending",
        gsm: Optional[int] = None,
        cost: Optional[float] = None,
        colors: Optional[List[str]] = None,
        fabric: Optional[str] = None,
        segment: Optional[str] = None,
        garment_type: Optional[str] = None,
        key_details: Optional[str] = None,
        category_name: Optional[str] = None,
        category_slug: Optional[str] = None,
        fabric_composition: Optional[str] = None,
        sheet_image: Optional[str] = None,
        swatch_image: Optional[str] = None,
        artwork_image: Optional[str] = None,
        garment_image: Optional[str] = None,
        theme_name: Optional[str] = None,
        theme_slug: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> ThemeStyle:
        """Create a new style record."""
        style = self.add_object(
            theme_id=theme_id,
            external_job_id=external_job_id,
            external_style_id=external_style_id,
            status=status,
            gsm=gsm,
            cost=cost,
            colors=colors,
            fabric=fabric,
            segment=segment,
            garment_type=garment_type,
            key_details=key_details,
            category_name=category_name,
            category_slug=category_slug,
            fabric_composition=fabric_composition,
            sheet_image=sheet_image,
            swatch_image=swatch_image,
            artwork_image=artwork_image,
            garment_image=garment_image,
            theme_name=theme_name,
            theme_slug=theme_slug,
            error_message=error_message,
        )
        await self._flush()
        return style

    async def bulk_create_styles(
        self,
        theme_id: UUID,
        external_job_id: str,
        styles_data: List[dict],
    ) -> List[ThemeStyle]:
        """
        Bulk create style records from webhook payload.

        Args:
            theme_id: UUID of the theme
            external_job_id: Job ID from Naruto API
            styles_data: List of style dictionaries from Naruto response

        Returns:
            List of created ThemeStyle objects
        """
        created_styles = []
        for style_data in styles_data:
            style = self.add_object(
                theme_id=theme_id,
                external_job_id=external_job_id,
                external_style_id=style_data.get("id"),
                status="completed",
                gsm=style_data.get("gsm"),
                cost=style_data.get("cost"),
                colors=style_data.get("colors"),
                fabric=style_data.get("fabric"),
                segment=style_data.get("segment"),
                garment_type=style_data.get("garment_type"),
                key_details=style_data.get("key_details"),
                category_name=style_data.get("category_name"),
                category_slug=style_data.get("category_slug"),
                fabric_composition=style_data.get("fabric_composition"),
                sheet_image=style_data.get("sheet_image"),
                swatch_image=style_data.get("swatch_image"),
                artwork_image=style_data.get("artwork_image"),
                garment_image=style_data.get("garment_image"),
                theme_name=style_data.get("theme_name"),
                theme_slug=style_data.get("theme_slug"),
            )
            created_styles.append(style)

        await self._flush()
        return created_styles

    async def get_by_id(self, style_id: UUID) -> Optional[ThemeStyle]:
        """Get style by ID."""
        query = select(ThemeStyle).where(ThemeStyle.id == style_id)
        result = await self._execute_query(query)
        return result.scalar_one_or_none()

    async def get_by_external_job_id(self, external_job_id: str) -> List[ThemeStyle]:
        """Get all styles for an external job ID from Naruto API."""
        query = (
            select(ThemeStyle)
            .where(ThemeStyle.external_job_id == external_job_id)
            .order_by(ThemeStyle.created_at.desc())
        )
        result = await self._execute_query(query)
        return list(result.scalars().all())

    async def get_by_theme_id(self, theme_id: UUID) -> List[ThemeStyle]:
        """Get all styles for a theme."""
        query = (
            select(ThemeStyle)
            .where(ThemeStyle.theme_id == theme_id)
            .order_by(ThemeStyle.created_at.desc())
        )
        result = await self._execute_query(query)
        return list(result.scalars().all())

    async def get_latest_by_theme_id(self, theme_id: UUID) -> Optional[ThemeStyle]:
        """Get the most recent style for a theme."""
        query = (
            select(ThemeStyle)
            .where(ThemeStyle.theme_id == theme_id)
            .order_by(ThemeStyle.created_at.desc())
            .limit(1)
        )
        result = await self._execute_query(query)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        style_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        external_job_id: Optional[str] = None,
    ) -> Optional[ThemeStyle]:
        """Update style status."""
        style = await self.get_by_id(style_id)
        if not style:
            return None

        style.status = status
        self.flag_modified(style, "status")

        if error_message is not None:
            style.error_message = error_message
            self.flag_modified(style, "error_message")

        if external_job_id is not None:
            style.external_job_id = external_job_id
            self.flag_modified(style, "external_job_id")

        await self._flush()
        return style

    async def update_designer_review(
        self,
        style_id: UUID,
        review_status: str,
    ) -> Optional[ThemeStyle]:
        """Update designer review status."""
        style = await self.get_by_id(style_id)
        if not style:
            return None

        style.designer_review = review_status
        self.flag_modified(style, "designer_review")

        await self._flush()
        return style

    async def update_showroom_review(
        self,
        style_id: UUID,
        review_status: str,
    ) -> Optional[ThemeStyle]:
        """Update showroom review status."""
        style = await self.get_by_id(style_id)
        if not style:
            return None

        style.showroom_review = review_status
        self.flag_modified(style, "showroom_review")

        await self._flush()
        return style

    async def mark_job_failed(
        self,
        style_id: UUID,
        error_message: str,
    ) -> Optional[ThemeStyle]:
        """Mark a style job as failed."""
        return await self.update_status(
            style_id=style_id,
            status="failed",
            error_message=error_message,
        )
