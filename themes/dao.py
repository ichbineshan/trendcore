"""
Theme Data Access Object.

Provides database operations for the Theme model.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from themes.models import Theme
from utils.dao import BaseDAO


class ThemeDAO(BaseDAO):
    """Data Access Object for Theme model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, db_model=Theme)

    async def create_theme(
        self,
        theme_id: UUID,
        collection_id: UUID,
        theme_name: str,
        theme_slug: str,
        generation_input: dict | None = None,
        status: str = "pending",
    ) -> Theme:
        """Create a new theme record."""
        theme = Theme(
            id=theme_id,
            collection_id=collection_id,
            theme_name=theme_name,
            theme_slug=theme_slug,
            generation_input=generation_input,
            status=status,
        )
        self.session.add(theme)
        return theme

    async def select_by_id(self, theme_id: UUID) -> Optional[Theme]:
        """Get theme by ID."""
        query = select(Theme).where(Theme.id == theme_id)
        result = await self._execute_query(query)
        return result.scalar_one_or_none()

    async def select_by_collection_id(self, collection_id: UUID) -> list[Theme]:
        """Get all themes for a collection."""
        query = (
            select(Theme)
            .where(Theme.collection_id == collection_id)
            .order_by(Theme.created_at)
        )
        result = await self._execute_query(query)
        return list(result.scalars().all())

    async def update_theme_generated_data(
        self,
        theme_id: UUID,
        # Basic Info
        theme_name: str | None = None,
        theme_slug: str | None = None,
        season_title: str | None = None,
        main_concept: str | None = None,
        one_line_summary: str | None = None,
        mood_tags: str | None = None,
        design_keywords: list | None = None,
        aesthetic_labels: list | None = None,
        is_aligned_to_brand_dna: bool | None = None,
        # Narrative
        key_story_points: str | None = None,
        lifestyle_context_notes: str | None = None,
        gender_or_inclusivity_notes: str | None = None,
        meaningful_color_associations: list | None = None,
        # Color Direction
        primary_colors: list | None = None,
        accent_colors: list | None = None,
        neutral_colors: list | None = None,
        palette_notes: list | None = None,
        palette: str | None = None,
        pantone_codes: list | None = None,
        coloro_codes: list | None = None,
        # Material & Silhouette
        fabric_notes: list | None = None,
        trim_keywords: list | None = None,
        print_keywords: list | None = None,
        important_fabrics: list | None = None,
        important_silhouettes: list | None = None,
        key_silhouettes: str | None = None,
        key_trend_fabrics: str | None = None,
        print_usage_guidelines: list | None = None,
        # Micro Trends
        print_placement_trends: list | None = None,
        wash_and_finish_trends: list | None = None,
        graphic_and_icon_trends: list | None = None,
        typography_micro_trends: list | None = None,
        fit_and_proportion_trends: list | None = None,
        other_micro_trend_signals: list | None = None,
        construction_detail_trends: list | None = None,
        accessory_and_styling_trends: list | None = None,
        # UI Suggestions
        fabric_suggestions: list | None = None,
        trim_suggestions: list | None = None,
        artwork_suggestions: list | None = None,
        # Moodboard
        moodboard_description: str | None = None,
    ) -> None:
        """Update theme with LLM-generated data."""
        update_values = {}

        # Basic Info
        if theme_name is not None:
            update_values["theme_name"] = theme_name
        if theme_slug is not None:
            update_values["theme_slug"] = theme_slug
        if season_title is not None:
            update_values["season_title"] = season_title
        if main_concept is not None:
            update_values["main_concept"] = main_concept
        if one_line_summary is not None:
            update_values["one_line_summary"] = one_line_summary
        if mood_tags is not None:
            update_values["mood_tags"] = mood_tags
        if design_keywords is not None:
            update_values["design_keywords"] = design_keywords
        if aesthetic_labels is not None:
            update_values["aesthetic_labels"] = aesthetic_labels
        if is_aligned_to_brand_dna is not None:
            update_values["is_aligned_to_brand_dna"] = is_aligned_to_brand_dna

        # Narrative
        if key_story_points is not None:
            update_values["key_story_points"] = key_story_points
        if lifestyle_context_notes is not None:
            update_values["lifestyle_context_notes"] = lifestyle_context_notes
        if gender_or_inclusivity_notes is not None:
            update_values["gender_or_inclusivity_notes"] = gender_or_inclusivity_notes
        if meaningful_color_associations is not None:
            update_values["meaningful_color_associations"] = meaningful_color_associations

        # Color Direction
        if primary_colors is not None:
            update_values["primary_colors"] = primary_colors
        if accent_colors is not None:
            update_values["accent_colors"] = accent_colors
        if neutral_colors is not None:
            update_values["neutral_colors"] = neutral_colors
        if palette_notes is not None:
            update_values["palette_notes"] = palette_notes
        if palette is not None:
            update_values["palette"] = palette
        if pantone_codes is not None:
            update_values["pantone_codes"] = pantone_codes
        if coloro_codes is not None:
            update_values["coloro_codes"] = coloro_codes

        # Material & Silhouette
        if fabric_notes is not None:
            update_values["fabric_notes"] = fabric_notes
        if trim_keywords is not None:
            update_values["trim_keywords"] = trim_keywords
        if print_keywords is not None:
            update_values["print_keywords"] = print_keywords
        if important_fabrics is not None:
            update_values["important_fabrics"] = important_fabrics
        if important_silhouettes is not None:
            update_values["important_silhouettes"] = important_silhouettes
        if key_silhouettes is not None:
            update_values["key_silhouettes"] = key_silhouettes
        if key_trend_fabrics is not None:
            update_values["key_trend_fabrics"] = key_trend_fabrics
        if print_usage_guidelines is not None:
            update_values["print_usage_guidelines"] = print_usage_guidelines

        # Micro Trends
        if print_placement_trends is not None:
            update_values["print_placement_trends"] = print_placement_trends
        if wash_and_finish_trends is not None:
            update_values["wash_and_finish_trends"] = wash_and_finish_trends
        if graphic_and_icon_trends is not None:
            update_values["graphic_and_icon_trends"] = graphic_and_icon_trends
        if typography_micro_trends is not None:
            update_values["typography_micro_trends"] = typography_micro_trends
        if fit_and_proportion_trends is not None:
            update_values["fit_and_proportion_trends"] = fit_and_proportion_trends
        if other_micro_trend_signals is not None:
            update_values["other_micro_trend_signals"] = other_micro_trend_signals
        if construction_detail_trends is not None:
            update_values["construction_detail_trends"] = construction_detail_trends
        if accessory_and_styling_trends is not None:
            update_values["accessory_and_styling_trends"] = accessory_and_styling_trends

        # UI Suggestions
        if fabric_suggestions is not None:
            update_values["fabric_suggestions"] = fabric_suggestions
        if trim_suggestions is not None:
            update_values["trim_suggestions"] = trim_suggestions
        if artwork_suggestions is not None:
            update_values["artwork_suggestions"] = artwork_suggestions

        # Moodboard
        if moodboard_description is not None:
            update_values["moodboard_description"] = moodboard_description

        # Always mark as completed when updating generated data
        update_values["status"] = "completed"

        if update_values:
            query = (
                update(Theme)
                .where(Theme.id == theme_id)
                .values(**update_values)
            )
            await self._execute_query(query)

    async def update_status(self, theme_id: UUID, status: str) -> None:
        """Update theme status."""
        query = (
            update(Theme)
            .where(Theme.id == theme_id)
            .values(status=status)
        )
        await self._execute_query(query)

    async def update_moodboard_image(self, theme_id: UUID, moodboard_image_url: str) -> None:
        """Update theme moodboard image URL."""
        query = (
            update(Theme)
            .where(Theme.id == theme_id)
            .values(moodboard_image_url=moodboard_image_url)
        )
        await self._execute_query(query)

    async def update_references(self, theme_id: UUID, references: list[str]) -> None:
        """Update theme references."""
        query = (
            update(Theme)
            .where(Theme.id == theme_id)
            .values(references=references)
        )
        await self._execute_query(query)

    async def bulk_update_status(self, collection_id: UUID, status: str) -> None:
        """Update status for all themes in a collection."""
        query = (
            update(Theme)
            .where(Theme.collection_id == collection_id)
            .values(status=status)
        )
        await self._execute_query(query)

    async def update_review_status(
            self,
            theme_id: UUID,
            review_status: str,
            review_notes: str | None = None,
    ) -> None:
        """Update theme review status and notes."""
        update_values = {"review_status": review_status}
        if review_notes is not None:
            update_values["review_notes"] = review_notes

        query = (
            update(Theme)
            .where(Theme.id == theme_id)
            .values(**update_values)
        )
        await self._execute_query(query)

