from typing import Any

from pydantic import BaseModel


# ============================================================================
# Visual Identity Schema
# ============================================================================

class BrandColorsGlobalPalette(BaseModel):
    overview: str
    master_palette: list[str]
    accessibility_notes: str


class VisualIdentity(BaseModel):
    brand_colors_global_palette: BrandColorsGlobalPalette


# ============================================================================
# Design Guardrails Schema
# ============================================================================

class DesignGuardrails(BaseModel):
    brand_should_do: list[str]
    brand_should_not_do: list[str]


# ============================================================================
# Market Positioning Schema
# ============================================================================

class TargetAudience(BaseModel):
    genders: list[str]
    regions: list[str]
    age_range: str
    psychographics: str
    style_archetypes: list[str]
    demographic_summary: str


class GlobalPriceRangeSummary(BaseModel):
    currency: str
    median_price: str
    maximum_price: str
    minimum_price: str


class MarketPositioning(BaseModel):
    brand_tier: str
    target_audience: TargetAudience
    brand_descriptive_tags: list[str]
    global_price_range_summary: GlobalPriceRangeSummary
    primary_product_categories: list[str]


# ============================================================================
# Cultural Influences Schema
# ============================================================================

class CulturalInfluences(BaseModel):
    cultural_references: list[str]
    language_or_script_usage: list[str]
    cultural_sensitivity_notes: str
    important_symbols_or_motifs: list[str]
    subculture_and_community_associations: list[str]
    festivals_or_occasions_influencing_design: list[str]


# ============================================================================
# Core Values and Voice Schema
# ============================================================================

class CoreValuesAndVoice(BaseModel):
    voice_style: str
    heritage_background: str
    design_theme_summary: str
    brand_values_and_tones: str
    brand_story_and_ideology: str


# ============================================================================
# Brand Reference Images Schema
# ============================================================================

class BrandReferenceImage(BaseModel):
    notes: str
    source: str
    image_id: str
    image_role: str
    image_type: str
    linked_topics: list[str]
    image_category: str


# ============================================================================
# API Request/Response Schemas
# ============================================================================

class BrandOnboardingRequest(BaseModel):
    """
    Dynamic payload for brand onboarding.
    Only brand_name is required, all other fields are stored in user_request.
    """
    brand_name: str

    class Config:
        extra = "allow"


class BrandOnboardingResponse(BaseModel):
    """Response for brand onboarding API."""
    success: bool
    message: str
    data: dict[str, Any] | None = None
    error: str | None = None
