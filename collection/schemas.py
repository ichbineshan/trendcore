from typing import Any

from pydantic import BaseModel


class CollectionCreateRequest(BaseModel):
    """
    Request payload for creating a collection.
    brand_id is required, all other fields stored in user_req.
    """
    brand_id: str

    class Config:
        extra = "allow"


class CollectionCreateResponse(BaseModel):
    """Response for collection creation API."""
    success: bool
    message: str
    data: dict[str, Any] | None = None
    error: str | None = None


class RangeOverviewStats(BaseModel):
    """Stats section of range overview."""
    categories: int
    styles: int
    themes: int


class RangeOverviewItem(BaseModel):
    """Single item in range overview table."""
    category: str
    brick: str
    style_fit: str
    num_styles: int
    price_range: str


class RangeOverview(BaseModel):
    """Complete range overview structure."""
    stats: RangeOverviewStats
    items: list[RangeOverviewItem]


class CollectionOverviewOutput(BaseModel):
    """LLM output schema for collection overview generation."""
    collection_name: str
    overview: str
    range_overview: RangeOverview


# ============================================================================
# GET Collection Overview Response Schemas
# ============================================================================

class NarrativeSection(BaseModel):
    """Narrative section of collection overview."""
    collection_name: str | None
    season: str | None
    overview: str | None


class TargetMarketSection(BaseModel):
    """Target & Market section of collection overview."""
    season_year: str | None
    market: str | None
    occasion: str | None
    gender: str | None
    design_mood: str | None
    design_details: list[str] | None


class CollectionOverviewData(BaseModel):
    """Complete collection overview data."""
    collection_id: str
    status: str
    image_url: str | None
    narrative: NarrativeSection
    range_overview: RangeOverview | None
    target_market: TargetMarketSection


class CollectionOverviewResponse(BaseModel):
    """Response for GET collection overview API."""
    success: bool
    message: str
    data: CollectionOverviewData | None = None
    error: str | None = None


class CollectionSummary(BaseModel):
    """Summary of a single collection."""
    collection_id: str
    collection_name: str | None
    status: str
    image_url: str | None
    created_at: int | None


class BrandCollectionsResponse(BaseModel):
    """Response for listing collections by brand."""
    success: bool
    message: str
    data: list[CollectionSummary] | None = None
    error: str | None = None
