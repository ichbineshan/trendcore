"""
Theme Trend Data Access Object.

Provides database operations for the ThemeTrend model.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from trend.models import ThemeTrend
from utils.dao import BaseDAO


class ThemeTrendDAO(BaseDAO):
    """Data Access Object for ThemeTrend model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, db_model=ThemeTrend)

    async def create_theme_trend(
        self,
        theme_trend_id: UUID,
        theme_id: UUID,
        status: str = "pending",
    ) -> ThemeTrend:
        """Create a new theme trend record."""
        theme_trend = ThemeTrend(
            id=theme_trend_id,
            theme_id=theme_id,
            status=status,
        )
        self.session.add(theme_trend)
        return theme_trend

    async def select_by_id(self, theme_trend_id: UUID) -> Optional[ThemeTrend]:
        """Get theme trend by ID."""
        query = select(ThemeTrend).where(ThemeTrend.id == theme_trend_id)
        result = await self._execute_query(query)
        return result.scalar_one_or_none()

    async def select_by_theme_id(self, theme_id: UUID) -> Optional[ThemeTrend]:
        """Get theme trend by theme ID."""
        query = select(ThemeTrend).where(ThemeTrend.theme_id == theme_id)
        result = await self._execute_query(query)
        return result.scalar_one_or_none()

    async def update_category_trends(
        self,
        theme_id: UUID,
        category_trends: dict,
    ) -> None:
        """Update category_trends JSONB and mark status as category_trends_done."""
        query = (
            update(ThemeTrend)
            .where(ThemeTrend.theme_id == theme_id)
            .values(
                category_trends=category_trends,
                status="category_trends_done",
            )
        )
        await self._execute_query(query)

    async def update_trend_spotting(
        self,
        theme_id: UUID,
        trend_spotting: dict,
    ) -> None:
        """Update trend_spotting JSONB and mark status as completed."""
        query = (
            update(ThemeTrend)
            .where(ThemeTrend.theme_id == theme_id)
            .values(
                trend_spotting=trend_spotting,
                status="completed",
            )
        )
        await self._execute_query(query)

    async def update_status(self, theme_id: UUID, status: str) -> None:
        """Update theme trend status."""
        query = (
            update(ThemeTrend)
            .where(ThemeTrend.theme_id == theme_id)
            .values(status=status)
        )
        await self._execute_query(query)

    async def mark_failed(self, theme_id: UUID) -> None:
        """Mark theme trend as failed."""
        await self.update_status(theme_id, "failed")
