"""
Theme Views for Collection DNA.

Request handlers for theme API endpoints.
"""

import logging
from typing import Any
from uuid import UUID

from themes.schemas import (
    ThemeTileData,
    ThemeTilesResponse,
    ThemeFullDetailData,
    ThemeDetailResponse,
    ThemeReviewRequest,
    ThemeReviewResponse,
)
from themes.service import ThemeService

logger = logging.getLogger(__name__)


async def get_theme_tiles(collection_id: str) -> dict[str, Any]:
    """
    Get theme tiles for a collection.

    Returns lightweight theme data for card/tile display:
    - id, theme_name, theme_slug, status
    - one_line_summary, mood_tags, aesthetic_labels
    - moodboard_image_url
    """
    try:
        themes = await ThemeService.get_themes_by_collection_id(UUID(collection_id))

        if not themes:
            return ThemeTilesResponse(
                success=True,
                message="No themes found for this collection",
                data=[],
            ).model_dump()

        tiles = [
            ThemeTileData(
                id=str(theme.id),
                theme_name=theme.theme_name,
                theme_slug=theme.theme_slug,
                status=theme.status,
                one_line_summary=theme.one_line_summary,
                mood_tags=theme.mood_tags,
                aesthetic_labels=theme.aesthetic_labels,
                #moodboard_image_url=theme.moodboard_image_url,
            )
            for theme in themes
        ]

        return ThemeTilesResponse(
            success=True,
            message=f"Retrieved {len(tiles)} themes",
            data=tiles,
        ).model_dump()

    except Exception as e:
        logger.exception(f"Failed to get theme tiles: {e}")
        return ThemeTilesResponse(
            success=False,
            message="Failed to get theme tiles",
            error=str(e),
        ).model_dump()


async def get_theme_detail(theme_id: str) -> dict[str, Any]:
    """
    Get full theme details by ID.

    Returns complete theme data including:
    - Basic info (name, concept, mood, keywords)
    - Trend narrative
    - Color direction with Pantone/Coloro codes
    - Material & silhouette direction
    - Micro trends
    - UI suggestions (fabric, trim, artwork)
    - Moodboard data
    """
    try:
        theme = await ThemeService.get_theme_by_id(UUID(theme_id))


        if not theme:
            return ThemeDetailResponse(
                success=False,
                message="Theme not found",
                error=f"No theme found with id: {theme_id}",
            ).model_dump()

        detail = ThemeFullDetailData(
            # Basic Info
            id=str(theme.id),
            collection_id=str(theme.collection_id),
            theme_name=theme.theme_name,
            theme_slug=theme.theme_slug,
            season_title=theme.season_title,
            main_concept=theme.main_concept,
            one_line_summary=theme.one_line_summary,
            mood_tags=theme.mood_tags,
            design_keywords=theme.design_keywords,
            aesthetic_labels=theme.aesthetic_labels,
            is_aligned_to_brand_dna=theme.is_aligned_to_brand_dna,
            # Trend Narrative
            key_story_points=theme.key_story_points,
            lifestyle_context_notes=theme.lifestyle_context_notes,
            gender_or_inclusivity_notes=theme.gender_or_inclusivity_notes,
            meaningful_color_associations=theme.meaningful_color_associations,
            # Color Direction
            primary_colors=theme.primary_colors,
            accent_colors=theme.accent_colors,
            neutral_colors=theme.neutral_colors,
            palette_notes=theme.palette_notes,
            palette=theme.palette,
            pantone_codes=theme.pantone_codes,
            coloro_codes=theme.coloro_codes,
            # Material & Silhouette Direction
            fabric_notes=theme.fabric_notes,
            trim_keywords=theme.trim_keywords,
            print_keywords=theme.print_keywords,
            important_fabrics=theme.important_fabrics,
            important_silhouettes=theme.important_silhouettes,
            key_silhouettes=theme.key_silhouettes,
            key_trend_fabrics=theme.key_trend_fabrics,
            print_usage_guidelines=theme.print_usage_guidelines,
            # Micro Trends
            print_placement_trends=theme.print_placement_trends,
            wash_and_finish_trends=theme.wash_and_finish_trends,
            graphic_and_icon_trends=theme.graphic_and_icon_trends,
            typography_micro_trends=theme.typography_micro_trends,
            fit_and_proportion_trends=theme.fit_and_proportion_trends,
            other_micro_trend_signals=theme.other_micro_trend_signals,
            construction_detail_trends=theme.construction_detail_trends,
            accessory_and_styling_trends=theme.accessory_and_styling_trends,
            # UI Suggestions
            fabric_suggestions=theme.fabric_suggestions,
            trim_suggestions=theme.trim_suggestions,
            artwork_suggestions=theme.artwork_suggestions,
            # Moodboard

            # Status
            status=theme.status,
            # Review Status
            review_status=theme.review_status,
            review_notes=theme.review_notes,
        )

        return ThemeDetailResponse(
            success=True,
            message="Theme details retrieved successfully",
            data=detail,
        ).model_dump()

    except Exception as e:
        logger.exception(f"Failed to get theme detail: {e}")
        return ThemeDetailResponse(
            success=False,
            message="Failed to get theme detail",
            error=str(e),
        ).model_dump()


async def update_theme_review(theme_id: str, request: ThemeReviewRequest) -> dict[str, Any]:
        """
        Update theme review status.

        Sets review_status to 'approved' or 'rejected' with optional notes.
        """
        try:
            theme = await ThemeService.update_review(
                theme_id=UUID(theme_id),
                review_status=request.review_status.value,
                review_notes=request.review_notes,
            )

            if not theme:
                return ThemeReviewResponse(
                    success=False,
                    message="Theme not found",
                    error=f"No theme found with id: {theme_id}",
                ).model_dump()

            return ThemeReviewResponse(
                success=True,
                message=f"Theme review status updated to '{request.review_status.value}'",
                data={
                    "id": str(theme.id),
                    "review_status": theme.review_status,
                    "review_notes": theme.review_notes,
                },
            ).model_dump()

        except Exception as e:
            logger.exception(f"Failed to update theme review: {e}")
            return ThemeReviewResponse(
                success=False,
                message="Failed to update theme review",
                error=str(e),
            ).model_dump()
