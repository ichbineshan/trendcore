"""
Theme Trend Service Layer.

Business logic for theme trend operations.
"""

from uuid import UUID

import uuid6

from trend.dao import ThemeTrendDAO
from trend.models import ThemeTrend
from config.logging import logger
from utils.connection_handler import get_connection_handler_for_app


class ThemeTrendService:
    """Service layer for ThemeTrend operations."""

    @staticmethod
    async def create_theme_trend(theme_id: UUID) -> UUID:
        """Create a new theme trend record with pending status."""
        theme_trend_id = uuid6.uuid7()

        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeTrendDAO(connection_handler.session)
            await dao.create_theme_trend(
                theme_trend_id=theme_trend_id,
                theme_id=theme_id,
                status="pending",
            )
            await connection_handler.session.commit()
            logger.info(
                f"Created theme trend record: {theme_trend_id}",
                extra={"theme_id": str(theme_id)},
            )

        return theme_trend_id

    @staticmethod
    async def get_by_theme_id(theme_id: UUID) -> ThemeTrend | None:
        """Get theme trend by theme ID."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeTrendDAO(connection_handler.session)
            return await dao.select_by_theme_id(theme_id)

    @staticmethod
    async def update_category_trends(
        theme_id: UUID,
        category_trends: dict,
    ) -> None:
        """Update category trends data and mark as category_trends_done."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeTrendDAO(connection_handler.session)
            await dao.update_category_trends(theme_id, category_trends)
            await connection_handler.session.commit()
            logger.info(
                "Updated category trends",
                extra={"theme_id": str(theme_id)},
            )

    @staticmethod
    async def update_trend_spotting(
        theme_id: UUID,
        trend_spotting: dict,
    ) -> None:
        """Update trend spotting data and mark as completed."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeTrendDAO(connection_handler.session)
            await dao.update_trend_spotting(theme_id, trend_spotting)
            await connection_handler.session.commit()
            logger.info(
                "Updated trend spotting",
                extra={"theme_id": str(theme_id)},
            )

    @staticmethod
    async def mark_failed(theme_id: UUID) -> None:
        """Mark theme trend as failed."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeTrendDAO(connection_handler.session)
            await dao.mark_failed(theme_id)
            await connection_handler.session.commit()
            logger.warning(
                "Marked theme trend as failed",
                extra={"theme_id": str(theme_id)},
            )
