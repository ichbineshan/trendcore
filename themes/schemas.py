"""
Theme Schemas for Collection DNA.

Pydantic schemas for theme generation, API requests/responses,
and LLM output validation.
"""

from typing import Any

from pydantic import BaseModel
from enum import Enum


class ReviewStatus(str, Enum):
    """Review status enum for API."""
    approved = "approved"
    rejected = "rejected"

# =============================================================================
# LLM Output Schemas (for theme generation)
# =============================================================================

class ColorDirection(BaseModel):
    """Color direction for a theme."""
    primary_colors: list[str] = []
    accent_colors: list[str] = []
    neutral_colors: list[str] = []
    palette_notes: list[str] = []
    palette: str = ""


class TrendNarrative(BaseModel):
    """Trend narrative for a theme."""
    key_story_points: str = ""


class MicroTrends(BaseModel):
    """Micro trends breakdown for a theme."""
    print_placement_trends: list[str] = []
    wash_and_finish_trends: list[str] = []
    graphic_and_icon_trends: list[str] = []
    typography_micro_trends: list[str] = []
    fit_and_proportion_trends: list[str] = []
    other_micro_trend_signals: list[str] = []
    construction_detail_trends: list[str] = []
    accessory_and_styling_trends: list[str] = []


class MaterialAndSilhouetteDirection(BaseModel):
    """Material and silhouette direction for a theme."""
    fabric_notes: list[str] = []
    trim_keywords: list[str] = []
    print_keywords: list[str] = []
    important_fabrics: list[str] = []
    important_silhouettes: list[str] = []
    key_silhouettes: str = ""
    key_trend_fabrics: str = ""
    print_usage_guidelines: list[str] = []


class UISuggestions(BaseModel):
    """UI-friendly suggestions for display in frontend."""
    fabric_suggestions: list[str] = []
    trim_suggestions: list[str] = []
    artwork_suggestions: list[str] = []


class ColorPalette(BaseModel):
    """Color palette with Pantone/Coloro codes."""
    pantone_codes: list[str] = []
    coloro_codes: list[str] = []
    palette_description: str = ""


class ThemeGenerationOutput(BaseModel):
    """Complete LLM output schema for theme generation."""
    # Basic Info
    theme_name: str
    theme_slug: str
    season_title: str
    main_concept: str
    one_line_summary: str
    mood_tags: str
    design_keywords: list[str]
    aesthetic_labels: list[str]
    is_aligned_to_brand_dna: bool

    # Narrative
    trend_narrative: TrendNarrative
    lifestyle_context_notes: str
    gender_or_inclusivity_notes: str
    meaningful_color_associations: list[str]

    # Color Direction
    color_direction: ColorDirection
    color_palette: ColorPalette

    # Material & Silhouette
    material_and_silhouette_direction: MaterialAndSilhouetteDirection

    # Micro Trends
    micro_trends: MicroTrends

    # UI Suggestions
    ui_suggestions: UISuggestions


class ThemesGenerationOutput(BaseModel):
    """Output schema for multiple themes generation."""
    themes: list[ThemeGenerationOutput]
    references: list[str] = []


# =============================================================================
# Phase 1: Theme Brief Schemas (for distinct theme generation)
# =============================================================================

class ThemeBrief(BaseModel):
    """
    Lightweight theme brief for Phase 1.

    Purpose: Establish distinct theme directions before detailed generation.
    """
    theme_name: str
    theme_slug: str
    core_concept: str  # 50-100 words - the essence of the theme
    key_differentiator: str  # What makes this theme unique from others
    color_direction_hint: str  # General color family (e.g., "warm earthy tones")
    mood_keywords: list[str]  # 3-5 mood descriptors
    material_direction_hint: str  # General fabric/texture direction
    reasoning: str  # Chain of thought - why this theme is distinct


class ThemeBriefsOutput(BaseModel):
    """Output schema for Phase 1 - multiple distinct briefs."""
    briefs: list[ThemeBrief]
    distinctiveness_rationale: str  # How the themes differ from each other


# =============================================================================
# API Request/Response Schemas
# =============================================================================

class ThemeCreateRequest(BaseModel):
    """Request to create themes for a collection."""
    collection_id: str
    theme_requirements: list[dict[str, Any]]


class ThemeReviewRequest(BaseModel):
    """Request to update theme review status."""
    review_status: ReviewStatus
    review_notes: str | None = None


class ThemeReviewResponse(BaseModel):
    """Response for theme review update."""
    success: bool
    message: str
    data: dict | None = None
    error: str | None = None

# -----------------------------------------------------------------------------
# Theme Tiles API Response (Lightweight for cards)
# -----------------------------------------------------------------------------

class ThemeTileData(BaseModel):
    """Lightweight theme data for tile/card display."""
    id: str
    theme_name: str
    theme_slug: str
    status: str
    one_line_summary: str | None = None
    mood_tags: str | None = None
    aesthetic_labels: list[str] | None = None
    moodboard_image_url: str | None = None


class ThemeTilesResponse(BaseModel):
    """Response for listing theme tiles."""
    success: bool
    message: str
    data: list[ThemeTileData] | None = None
    error: str | None = None


# -----------------------------------------------------------------------------
# Theme Detail API Response (Full details)
# -----------------------------------------------------------------------------

class ThemeFullDetailData(BaseModel):
    """Complete theme data for detail view."""
    # Basic Info
    id: str
    collection_id: str
    theme_name: str
    theme_slug: str
    season_title: str | None = None
    main_concept: str | None = None
    one_line_summary: str | None = None
    mood_tags: str | None = None
    design_keywords: list[str] | None = None
    aesthetic_labels: list[str] | None = None
    is_aligned_to_brand_dna: bool | None = None

    # Trend Narrative
    key_story_points: str | None = None
    lifestyle_context_notes: str | None = None
    gender_or_inclusivity_notes: str | None = None
    meaningful_color_associations: list[str] | None = None

    # Color Direction
    primary_colors: list[str] | None = None
    accent_colors: list[str] | None = None
    neutral_colors: list[str] | None = None
    palette_notes: list[str] | None = None
    palette: str | None = None
    pantone_codes: list[str] | None = None
    coloro_codes: list[str] | None = None

    # Material & Silhouette Direction
    fabric_notes: list[str] | None = None
    trim_keywords: list[str] | None = None
    print_keywords: list[str] | None = None
    important_fabrics: list[str] | None = None
    important_silhouettes: list[str] | None = None
    key_silhouettes: str | None = None
    key_trend_fabrics: str | None = None
    print_usage_guidelines: list[str] | None = None

    # Micro Trends
    print_placement_trends: list[str] | None = None
    wash_and_finish_trends: list[str] | None = None
    graphic_and_icon_trends: list[str] | None = None
    typography_micro_trends: list[str] | None = None
    fit_and_proportion_trends: list[str] | None = None
    other_micro_trend_signals: list[str] | None = None
    construction_detail_trends: list[str] | None = None
    accessory_and_styling_trends: list[str] | None = None

    # UI Suggestions
    fabric_suggestions: list[str] | None = None
    trim_suggestions: list[str] | None = None
    artwork_suggestions: list[str] | None = None

    # Moodboard
    moodboard_description: str | None = None
    moodboard_image_url: str | None = None

    # Status
    status: str


class ThemeDetailResponse(BaseModel):
    """Response for single theme detail."""
    success: bool
    message: str
    data: ThemeFullDetailData | None = None
    error: str | None = None


# -----------------------------------------------------------------------------
# Legacy schemas (kept for backward compatibility)
# -----------------------------------------------------------------------------

class ThemeResponse(BaseModel):
    """Single theme response for API (legacy)."""
    id: str
    collection_id: str
    theme_name: str
    theme_slug: str
    season_title: str | None
    main_concept: str | None
    one_line_summary: str | None
    mood_tags: str | None
    design_keywords: list[str] | None
    aesthetic_labels: list[str] | None

    # Color Palette
    pantone_codes: list[str] | None
    coloro_codes: list[str] | None
    palette: str | None

    # UI Suggestions
    fabric_suggestions: list[str] | None
    trim_suggestions: list[str] | None
    artwork_suggestions: list[str] | None

    # Moodboard
    moodboard_description: str | None
    moodboard_image_url: str | None

    # Status
    status: str
