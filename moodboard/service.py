"""
Moodboard Service Layer.

Business logic for moodboard operations.
"""

from uuid import UUID

from moodboard.dao import ThemeMoodboardDAO
from moodboard.models import ThemeMoodboard
from config.logging import logger
from utils.connection_handler import get_connection_handler_for_app


class MoodboardService:
    """Service layer for ThemeMoodboard operations."""

    @staticmethod
    async def create_moodboard(theme_id: UUID) -> UUID:
        """Create a new moodboard record with pending status."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeMoodboardDAO(connection_handler.session)
            moodboard = await dao.create_moodboard(
                theme_id=theme_id,
                status="pending",
            )
            await connection_handler.session.commit()
            logger.info(
                f"Created moodboard record: {moodboard.id}",
                extra={"theme_id": str(theme_id)},
            )
            return moodboard.id

    @staticmethod
    async def get_by_id(moodboard_id: UUID) -> ThemeMoodboard | None:
        """Get moodboard by ID."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeMoodboardDAO(connection_handler.session)
            return await dao.select_by_id(moodboard_id)

    @staticmethod
    async def get_by_theme_id(theme_id: UUID) -> ThemeMoodboard | None:
        """Get moodboard by theme ID."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeMoodboardDAO(connection_handler.session)
            return await dao.select_by_theme_id(theme_id)

    @staticmethod
    async def update_collage_data(
        moodboard_id: UUID,
        moodboard_slug: str,
        collage_prompt: str,
        collage_reference_images: list[str],
    ) -> None:
        """Update moodboard with collage generation data."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeMoodboardDAO(connection_handler.session)
            await dao.update_collage_data(
                moodboard_id=moodboard_id,
                moodboard_slug=moodboard_slug,
                collage_prompt=collage_prompt,
                collage_reference_images=collage_reference_images,
            )
            await connection_handler.session.commit()
            logger.info(
                "Updated collage data",
                extra={"moodboard_id": str(moodboard_id)},
            )

    @staticmethod
    async def update_element_prompts(
        moodboard_id: UUID,
        element_prompts: list[str],
    ) -> None:
        """Update moodboard with element prompts."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeMoodboardDAO(connection_handler.session)
            await dao.update_element_prompts(
                moodboard_id=moodboard_id,
                element_prompts=element_prompts,
            )
            await connection_handler.session.commit()
            logger.info(
                f"Updated element prompts ({len(element_prompts)} elements)",
                extra={"moodboard_id": str(moodboard_id)},
            )

    @staticmethod
    async def update_collage_image_url(
        moodboard_id: UUID,
        collage_image_url: str,
    ) -> None:
        """Update moodboard with generated collage image URL."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeMoodboardDAO(connection_handler.session)
            await dao.update_collage_image_url(
                moodboard_id=moodboard_id,
                collage_image_url=collage_image_url,
            )
            await connection_handler.session.commit()
            logger.info(
                "Updated collage image URL",
                extra={"moodboard_id": str(moodboard_id)},
            )

    @staticmethod
    async def update_element_image_urls(
        moodboard_id: UUID,
        element_image_urls: list[str],
    ) -> None:
        """Update moodboard with generated element image URLs."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeMoodboardDAO(connection_handler.session)
            await dao.update_element_image_urls(
                moodboard_id=moodboard_id,
                element_image_urls=element_image_urls,
            )
            await connection_handler.session.commit()
            logger.info(
                f"Updated element image URLs ({len(element_image_urls)} URLs)",
                extra={"moodboard_id": str(moodboard_id)},
            )

    @staticmethod
    async def update_status(moodboard_id: UUID, status: str) -> None:
        """Update moodboard status by ID."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeMoodboardDAO(connection_handler.session)
            await dao.update_status(moodboard_id, status)
            await connection_handler.session.commit()
            logger.info(
                f"Updated moodboard status to: {status}",
                extra={"moodboard_id": str(moodboard_id)},
            )

    @staticmethod
    async def mark_completed(moodboard_id: UUID) -> None:
        """Mark moodboard as completed."""
        await MoodboardService.update_status(moodboard_id, "completed")

    @staticmethod
    async def mark_failed(moodboard_id: UUID) -> None:
        """Mark moodboard as failed."""
        await MoodboardService.update_status(moodboard_id, "failed")
        logger.warning(
            "Marked moodboard as failed",
            extra={"moodboard_id": str(moodboard_id)},
        )

    @staticmethod
    async def mark_failed_by_theme_id(theme_id: UUID) -> None:
        """Mark moodboard as failed by theme ID."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeMoodboardDAO(connection_handler.session)
            await dao.update_status_by_theme_id(theme_id, "failed")
            await connection_handler.session.commit()
            logger.warning(
                "Marked moodboard as failed",
                extra={"theme_id": str(theme_id)},
            )
