"""
Theme Trend Schemas.

Pydantic schemas for trend data structures.
"""

from typing import Optional
from pydantic import BaseModel


# =============================================================================
# Category Trends Schemas (from category_trends.py)
# =============================================================================

class CategoryDesignLanguage(BaseModel):
    """Design language for a category."""
    trims: str
    fabric: str
    silhouette: str
    modesty_level: str
    print_and_graphics: str


class CategoryVisualIdentity(BaseModel):
    """Visual identity for a category."""
    visual_notes: str
    accent_colors: list[str]
    dominant_colors: list[str]


class CategoryMicroTrendsStatic(BaseModel):
    """Static micro trends for a category."""
    styling: str
    placement: str


class CategoryStaticSpec(BaseModel):
    """Static specification for a category."""
    category_design_language: CategoryDesignLanguage
    category_visual_identity: CategoryVisualIdentity
    category_micro_trends_static: CategoryMicroTrendsStatic


class PrintOverview(BaseModel):
    """Print overview for visual analysis."""
    print_style_tags: list[str]
    print_techniques: list[str]
    primary_print_families: list[str]
    secondary_print_families: list[str]


class MicroTrendTags(BaseModel):
    """Micro trend tags."""
    color_micro_trends: list[str]
    print_micro_trends: list[str]
    detail_micro_trends: list[str]
    placement_micro_trends: list[str]


class MotifVocabularyItem(BaseModel):
    """Individual motif vocabulary item."""
    scale: str
    density: str
    colorways: str
    motif_type: str
    edge_treatment: str
    spacing_pattern: str
    motif_description: str


class ColorStoryAnalysis(BaseModel):
    """Color story analysis."""
    contrast_behaviors: list[str]
    colorblocking_notes: str
    common_print_colors: list[str]
    dominant_base_colors: list[str]


class TextAndLogoPatterns(BaseModel):
    """Text and logo patterns."""
    logo_styles: list[str]
    typography_approaches: list[str]
    common_text_placements: list[str]


class ConstructionAndDetails(BaseModel):
    """Construction and details."""
    print_cutoff_patterns: str
    border_and_trim_patterns: list[str]
    feature_placement_strategies: list[str]


class PrintPlacementPatternsItem(BaseModel):
    """Print placement pattern item."""
    side: str
    zone: str
    notes: str
    orientation: str
    coverage_description: str
    alignment_with_garment: str


class CategoryVisualAnalysis(BaseModel):
    """Visual analysis for a category."""
    print_overview: PrintOverview
    micro_trend_tags: MicroTrendTags
    motif_vocabulary: list[MotifVocabularyItem]
    color_story_analysis: ColorStoryAnalysis
    category_trend_summary: str
    text_and_logo_patterns: TextAndLogoPatterns
    construction_and_details: ConstructionAndDetails
    print_placement_patterns: list[PrintPlacementPatternsItem]


class CategoryItem(BaseModel):
    """Individual category item."""
    name: str
    theme_slug: str
    gender: str
    age_range: str
    category_static_spec: CategoryStaticSpec
    category_visual_analysis: CategoryVisualAnalysis


class CategoryTrendsData(BaseModel):
    """Category trends data structure."""
    categories: list[CategoryItem]


# =============================================================================
# Trend Spotting Schemas (from trend_spotting.py)
# =============================================================================

class MetricItem(BaseModel):
    """Individual metric with label, value, and description."""
    label: str
    value: int | float | str | None
    formatted: str
    description: Optional[str] = None


class TopSearchItem(BaseModel):
    """Top search term with UI-friendly formatting."""
    term: str
    searches: str
    trend: str
    buyer_intent: str


class CommercialSummary(BaseModel):
    """Summary section for quick glance insights."""
    market_size: str
    market_size_value: str
    growth_trend: str
    commercial_potential: str
    confidence: str


class CommercialMetrics(BaseModel):
    """Detailed metrics section."""
    monthly_searches: MetricItem
    audience_reach: MetricItem
    buyer_intent: MetricItem
    ad_value: MetricItem


class CommercialValidation(BaseModel):
    """Commercial validation data from Ahrefs."""
    summary: CommercialSummary
    metrics: CommercialMetrics
    top_searches: list[TopSearchItem]
    data_date: Optional[str] = None
    error: Optional[str] = None


class TrendItem(BaseModel):
    """Individual trend item."""
    trend_name: str
    concept: str
    focus_items: list[str]
    key_takeaways: list[str]
    market_validation: list[str]
    commercial_validation: CommercialValidation
    mood: str


class TrendSpottingData(BaseModel):
    """Trend spotting data structure."""
    season: str
    trends: list[TrendItem]


# =============================================================================
# API Response Schemas
# =============================================================================

class ThemeTrendResponse(BaseModel):
    """API response for theme trend data."""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None
