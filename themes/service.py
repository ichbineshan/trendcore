"""
Theme Service Layer.

Business logic for theme operations.
"""

from uuid import UUID

import uuid6

from themes.dao import ThemeDAO
from themes.models import Theme
from themes.schemas import ThemeGenerationOutput
from config.logging import logger
from utils.connection_handler import get_connection_handler_for_app


class ThemeService:
    """Service layer for Theme operations."""

    @staticmethod
    async def create_theme(
        collection_id: UUID,
        theme_name: str,
        theme_slug: str,
        generation_input: dict | None = None,
    ) -> UUID:
        """Create a new theme record with pending status."""
        theme_id = uuid6.uuid7()

        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeDAO(connection_handler.session)
            await dao.create_theme(
                theme_id=theme_id,
                collection_id=collection_id,
                theme_name=theme_name,
                theme_slug=theme_slug,
                generation_input=generation_input,
                status="pending",
            )
            await connection_handler.session.commit()
            logger.info(f"Created new theme: {theme_id}")

        return theme_id

    @staticmethod
    async def create_themes_from_requirements(
        collection_id: UUID,
        theme_requirements: list[dict],
        season_title: str,
    ) -> list[UUID]:
        """
        Create placeholder theme records from requirements.

        Creates one theme record per requirement with pending status.
        Actual data will be populated by the generation activity.
        """
        theme_ids = []

        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeDAO(connection_handler.session)

            for idx, requirement in enumerate(theme_requirements):
                theme_id = uuid6.uuid7()
                # Generate placeholder name and slug
                theme_name = f"Theme {idx + 1}"
                theme_slug = f"theme-{idx + 1}"

                await dao.create_theme(
                    theme_id=theme_id,
                    collection_id=collection_id,
                    theme_name=theme_name,
                    theme_slug=theme_slug,
                    generation_input=requirement,
                    status="pending",
                )
                theme_ids.append(theme_id)

            await connection_handler.session.commit()
            logger.info(f"Created {len(theme_ids)} theme placeholders for collection {collection_id}")

        return theme_ids

    @staticmethod
    async def get_theme_by_id(theme_id: UUID) -> Theme | None:
        """Get theme by ID."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeDAO(connection_handler.session)
            return await dao.select_by_id(theme_id)

    @staticmethod
    async def get_themes_by_collection_id(collection_id: UUID) -> list[Theme]:
        """Get all themes for a collection."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeDAO(connection_handler.session)
            return await dao.select_by_collection_id(collection_id)

    @staticmethod
    async def update_theme_with_generated_data(
        theme_id: UUID,
        generated_data: ThemeGenerationOutput,
    ) -> None:
        """Update theme with LLM-generated data."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeDAO(connection_handler.session)
            await dao.update_theme_generated_data(
                theme_id=theme_id,
                # Basic Info
                theme_name=generated_data.theme_name,
                theme_slug=generated_data.theme_slug,
                season_title=generated_data.season_title,
                main_concept=generated_data.main_concept,
                one_line_summary=generated_data.one_line_summary,
                mood_tags=generated_data.mood_tags,
                design_keywords=generated_data.design_keywords,
                aesthetic_labels=generated_data.aesthetic_labels,
                is_aligned_to_brand_dna=generated_data.is_aligned_to_brand_dna,
                # Narrative
                key_story_points=generated_data.trend_narrative.key_story_points,
                lifestyle_context_notes=generated_data.lifestyle_context_notes,
                gender_or_inclusivity_notes=generated_data.gender_or_inclusivity_notes,
                meaningful_color_associations=generated_data.meaningful_color_associations,
                # Color Direction
                primary_colors=generated_data.color_direction.primary_colors,
                accent_colors=generated_data.color_direction.accent_colors,
                neutral_colors=generated_data.color_direction.neutral_colors,
                palette_notes=generated_data.color_direction.palette_notes,
                palette=generated_data.color_direction.palette,
                # Pantone/Coloro codes
                pantone_codes=generated_data.color_palette.pantone_codes,
                coloro_codes=generated_data.color_palette.coloro_codes,
                # Material & Silhouette Direction
                fabric_notes=generated_data.material_and_silhouette_direction.fabric_notes,
                trim_keywords=generated_data.material_and_silhouette_direction.trim_keywords,
                print_keywords=generated_data.material_and_silhouette_direction.print_keywords,
                important_fabrics=generated_data.material_and_silhouette_direction.important_fabrics,
                important_silhouettes=generated_data.material_and_silhouette_direction.important_silhouettes,
                key_silhouettes=generated_data.material_and_silhouette_direction.key_silhouettes,
                key_trend_fabrics=generated_data.material_and_silhouette_direction.key_trend_fabrics,
                print_usage_guidelines=generated_data.material_and_silhouette_direction.print_usage_guidelines,
                # Micro Trends
                print_placement_trends=generated_data.micro_trends.print_placement_trends,
                wash_and_finish_trends=generated_data.micro_trends.wash_and_finish_trends,
                graphic_and_icon_trends=generated_data.micro_trends.graphic_and_icon_trends,
                typography_micro_trends=generated_data.micro_trends.typography_micro_trends,
                fit_and_proportion_trends=generated_data.micro_trends.fit_and_proportion_trends,
                other_micro_trend_signals=generated_data.micro_trends.other_micro_trend_signals,
                construction_detail_trends=generated_data.micro_trends.construction_detail_trends,
                accessory_and_styling_trends=generated_data.micro_trends.accessory_and_styling_trends,
                # UI Suggestions
                fabric_suggestions=generated_data.ui_suggestions.fabric_suggestions,
                trim_suggestions=generated_data.ui_suggestions.trim_suggestions,
                artwork_suggestions=generated_data.ui_suggestions.artwork_suggestions,
            )
            await connection_handler.session.commit()
            logger.info(f"Updated theme with generated data: {theme_id}")

    @staticmethod
    async def update_theme_status(theme_id: UUID, status: str) -> None:
        """Update theme status."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeDAO(connection_handler.session)
            await dao.update_status(theme_id, status)
            await connection_handler.session.commit()

    @staticmethod
    async def update_moodboard_image(theme_id: UUID, image_url: str) -> None:
        """Update theme moodboard image URL."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeDAO(connection_handler.session)
            await dao.update_moodboard_image(theme_id, image_url)
            await connection_handler.session.commit()

    @staticmethod
    async def mark_themes_failed(collection_id: UUID) -> None:
        """Mark all themes in a collection as failed."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeDAO(connection_handler.session)
            await dao.bulk_update_status(collection_id, "failed")
            await connection_handler.session.commit()

    @staticmethod
    async def update_references(theme_id: UUID, references: list[str]) -> None:
        """Update theme references."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeDAO(connection_handler.session)
            await dao.update_references(theme_id, references)
            await connection_handler.session.commit()

    @staticmethod
    async def update_review(
            theme_id: UUID,
            review_status: str,
            review_notes: str | None = None,
    ) -> Theme | None:
        """Update theme review status and notes."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = ThemeDAO(connection_handler.session)

            # Check if theme exists
            theme = await dao.select_by_id(theme_id)
            if not theme:
                return None

            await dao.update_review_status(theme_id, review_status, review_notes)
            await connection_handler.session.commit()
            logger.info(f"Updated review status for theme {theme_id}: {review_status}")

            # Return updated theme
            return await dao.select_by_id(theme_id)

