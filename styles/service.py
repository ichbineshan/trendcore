"""
Style Generation Service.

Handles triggering style generation via Naruto API and processing webhook callbacks.
"""

import asyncio
import random
from typing import Optional, List
from uuid import UUID

from config.logging import logger
from config.settings import loaded_config
from styles.dao import StyleDAO
from styles.models import ThemeStyle
from styles.schemas import StyleWebhookPayload, ReviewStatus
from themes.dao import ThemeDAO
from styles.http_client import NarutoAPIClient, NarutoServiceError
from utils.connection_handler import get_connection_handler_for_app


class StyleGenerationService:
    """
    Service layer for style generation operations.
    """

    MAX_RETRIES = 3
    BASE_DELAY_SECONDS = 2

    @staticmethod
    async def trigger_style_workflow(theme_id: UUID) -> ThemeStyle:
        """
        Trigger style generation workflow for a given theme.

        Creates a placeholder style record and calls Naruto API.
        Actual styles are created when webhook is received.

        Args:
            theme_id: UUID of the theme

        Returns:
            Created placeholder ThemeStyle object

        Raises:
            ValueError: If theme not found
            NarutoServiceError: If Naruto API fails after all retries
        """
        async with get_connection_handler_for_app() as connection_handler:
            theme_dao = ThemeDAO(connection_handler.session)
            theme = await theme_dao.select_by_id(theme_id)

            if not theme:
                raise ValueError(f"Theme not found: {theme_id}")

            # Build theme data to send to Naruto
            theme_data = {
                "theme_id": str(theme.id),
                "collection_id": str(theme.collection_id),
                "theme_name": theme.theme_name,
                "theme_slug": theme.theme_slug,
                "season_title": theme.season_title,
                "main_concept": theme.main_concept,
                "one_line_summary": theme.one_line_summary,
                "mood_tags": theme.mood_tags,
                "design_keywords": theme.design_keywords,
                "aesthetic_labels": theme.aesthetic_labels,
                "is_aligned_to_brand_dna": theme.is_aligned_to_brand_dna,
                "key_story_points": theme.key_story_points,
                "lifestyle_context_notes": theme.lifestyle_context_notes,
                "gender_or_inclusivity_notes": theme.gender_or_inclusivity_notes,
                "primary_colors": theme.primary_colors,
                "accent_colors": theme.accent_colors,
                "neutral_colors": theme.neutral_colors,
                "palette_notes": theme.palette_notes,
                "palette": theme.palette,
                "meaningful_color_associations": theme.meaningful_color_associations,
                "pantone_codes": theme.pantone_codes,
                "coloro_codes": theme.coloro_codes,
                "fabric_notes": theme.fabric_notes,
                "trim_keywords": theme.trim_keywords,
                "print_keywords": theme.print_keywords,
                "important_fabrics": theme.important_fabrics,
                "important_silhouettes": theme.important_silhouettes,
                "key_silhouettes": theme.key_silhouettes,
                "key_trend_fabrics": theme.key_trend_fabrics,
                "print_usage_guidelines": theme.print_usage_guidelines,
                "print_placement_trends": theme.print_placement_trends,
                "wash_and_finish_trends": theme.wash_and_finish_trends,
                "graphic_and_icon_trends": theme.graphic_and_icon_trends,
                "typography_micro_trends": theme.typography_micro_trends,
                "fit_and_proportion_trends": theme.fit_and_proportion_trends,
                "other_micro_trend_signals": theme.other_micro_trend_signals,
                "construction_detail_trends": theme.construction_detail_trends,
                "accessory_and_styling_trends": theme.accessory_and_styling_trends,
                "fabric_suggestions": theme.fabric_suggestions,
                "trim_suggestions": theme.trim_suggestions,
                "artwork_suggestions": theme.artwork_suggestions,
                "generation_input": theme.generation_input,
                "references": theme.references,
            }

            # Create placeholder style record to track the job
            style_dao = StyleDAO(connection_handler.session)
            style = await style_dao.create_style(
                theme_id=theme_id,
                status="pending",
            )

            await connection_handler.session.commit()
            style_id = style.id

        # Build webhook URL with style_id
        webhook_url = f"https://api.fexz0.de/service/nighteye_hooks/v2.0/styles/webhook/{str(style_id)}"
        naruto_client = NarutoAPIClient(loaded_config.naruto_api_base_url)

        # Retry loop with exponential backoff
        for attempt in range(1, StyleGenerationService.MAX_RETRIES + 1):
            try:
                response = await naruto_client.trigger_design_generation(
                    design_brief=theme_data,
                    webhook_url=webhook_url,
                )

                external_job_id = response.get('job_id') or response.get('id')

                async with get_connection_handler_for_app() as connection_handler:
                    style_dao = StyleDAO(connection_handler.session)
                    await style_dao.update_status(
                        style_id=style_id,
                        status="processing",
                        external_job_id=str(external_job_id) if external_job_id else None,
                    )
                    await connection_handler.session.commit()

                logger.info(
                    f"Style workflow triggered successfully: "
                    f"style_id={str(style_id)}, external_job_id={external_job_id}"
                )

                async with get_connection_handler_for_app() as connection_handler:
                    style_dao = StyleDAO(connection_handler.session)
                    style = await style_dao.get_by_id(style_id)

                return style

            except NarutoServiceError as e:
                if attempt < StyleGenerationService.MAX_RETRIES:
                    delay = (
                        StyleGenerationService.BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                        + random.uniform(0, 1)
                    )
                    logger.warning(
                        f"Naruto API error (attempt {attempt}/{StyleGenerationService.MAX_RETRIES}), "
                        f"retrying in {delay:.2f}s: status_code={e.status_code}, "
                        f"style_id={str(style_id)}, theme_id={str(theme_id)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Naruto API failed after {StyleGenerationService.MAX_RETRIES} attempts: "
                        f"status_code={e.status_code}, style_id={str(style_id)}, "
                        f"theme_id={str(theme_id)}, error={e.message}"
                    )
                    async with get_connection_handler_for_app() as connection_handler:
                        style_dao = StyleDAO(connection_handler.session)
                        await style_dao.update_status(
                            style_id=style_id,
                            status="failed",
                            error_message=f"Naruto service unavailable after {StyleGenerationService.MAX_RETRIES} retries: {e}",
                        )
                        await connection_handler.session.commit()
                    raise

            except Exception as e:
                logger.error(
                    f"Style workflow error: style_id={str(style_id)}, "
                    f"theme_id={str(theme_id)}, error={str(e)}"
                )
                async with get_connection_handler_for_app() as connection_handler:
                    style_dao = StyleDAO(connection_handler.session)
                    await style_dao.update_status(
                        style_id=style_id,
                        status="failed",
                        error_message=str(e),
                    )
                    await connection_handler.session.commit()
                raise

    @staticmethod
    async def get_style_by_id(style_id: UUID) -> Optional[ThemeStyle]:
        """Get style by ID."""
        async with get_connection_handler_for_app() as connection_handler:
            style_dao = StyleDAO(connection_handler.session)
            return await style_dao.get_by_id(style_id)

    @staticmethod
    async def get_styles_by_theme_id(theme_id: UUID) -> List[ThemeStyle]:
        """Get all styles for a theme."""
        async with get_connection_handler_for_app() as connection_handler:
            style_dao = StyleDAO(connection_handler.session)
            return await style_dao.get_by_theme_id(theme_id)

    @staticmethod
    async def process_webhook_callback(
        style_id: str,
        payload: StyleWebhookPayload,
    ) -> List[ThemeStyle]:
        """
        Process webhook callback from Naruto API.

        Creates individual style rows from the styles array in the payload.
        The original placeholder style is updated to mark the job as complete.

        Args:
            style_id: UUID string of the placeholder style from URL path
            payload: Webhook payload from Naruto API

        Returns:
            List of created ThemeStyle objects, empty list if job failed
        """
        async with get_connection_handler_for_app() as connection_handler:
            style_dao = StyleDAO(connection_handler.session)

            try:
                style_uuid = UUID(style_id)
            except (ValueError, AttributeError) as e:
                logger.error(f"Invalid style_id format: {style_id}, error: {str(e)}")
                return []

            # Get the placeholder style to retrieve theme_id
            placeholder_style = await style_dao.get_by_id(style_uuid)

            if not placeholder_style:
                logger.warning(f"No placeholder style found for style_id={style_id}")
                return []

            theme_id = placeholder_style.theme_id

            # Handle failed job
            if payload.status == "failed" or payload.error:
                await style_dao.update_status(
                    style_id=style_uuid,
                    status="failed",
                    error_message=payload.error or "Job failed",
                )
                await connection_handler.session.commit()
                logger.warning(
                    f"Style job failed: style_id={style_id}, error={payload.error}"
                )
                return []

            # Create individual style rows from the styles array
            created_styles = []
            if payload.styles:
                created_styles = await style_dao.bulk_create_styles(
                    theme_id=theme_id,
                    external_job_id=payload.job_id,
                    styles_data=payload.styles,
                )

                logger.info(
                    f"Created {len(created_styles)} styles from webhook: "
                    f"style_id={style_id}, job_id={payload.job_id}"
                )

            # Update placeholder to completed
            await style_dao.update_status(
                style_id=style_uuid,
                status="completed",
                external_job_id=payload.job_id,
            )

            await connection_handler.session.commit()

            logger.info(
                f"Style webhook processed: style_id={style_id}, status={payload.status}, "
                f"styles_created={len(created_styles)}"
            )

            return created_styles

    @staticmethod
    async def update_designer_review(
        style_id: UUID,
        review_status: ReviewStatus,
    ) -> Optional[ThemeStyle]:
        """Update designer review status for a style."""
        async with get_connection_handler_for_app() as connection_handler:
            style_dao = StyleDAO(connection_handler.session)
            style = await style_dao.update_designer_review(
                style_id=style_id,
                review_status=review_status.value,
            )
            await connection_handler.session.commit()

            if style:
                logger.info(
                    f"Designer review updated: style_id={str(style_id)}, "
                    f"status={review_status.value}"
                )

            return style

    @staticmethod
    async def update_showroom_review(
        style_id: UUID,
        review_status: ReviewStatus,
    ) -> Optional[ThemeStyle]:
        """Update showroom review status for a style."""
        async with get_connection_handler_for_app() as connection_handler:
            style_dao = StyleDAO(connection_handler.session)
            style = await style_dao.update_showroom_review(
                style_id=style_id,
                review_status=review_status.value,
            )
            await connection_handler.session.commit()

            if style:
                logger.info(
                    f"Showroom review updated: style_id={str(style_id)}, "
                    f"status={review_status.value}"
                )

            return style

    @staticmethod
    async def mark_style_failed(style_id: UUID, error_message: str) -> Optional[ThemeStyle]:
        """Mark a style job as failed."""
        async with get_connection_handler_for_app() as connection_handler:
            style_dao = StyleDAO(connection_handler.session)
            style = await style_dao.mark_job_failed(
                style_id=style_id,
                error_message=error_message,
            )
            await connection_handler.session.commit()
            return style
