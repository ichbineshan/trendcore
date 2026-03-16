"""
Moodboard Pydantic Schemas.

Defines schemas for:
- LLM output parsing (MoodboardCollageOutput, MoodboardElementsOutput)
- API responses (if needed in future)
"""

from pydantic import BaseModel, Field


# =============================================================================
# LLM Output Schemas
# =============================================================================

class MoodboardCollageOutput(BaseModel):
    """
    Schema for collage generation LLM output.

    The moodboard description is a detailed prompt for generating
    a collage image that captures the theme's visual direction.
    """
    moodboard: str = Field(
        ...,
        description="Detailed description of the moodboard collage, including layout, "
                    "element placement, colors, fabrics, and visual composition."
    )
    reference_images: str = Field(
        ...,
        description="Comma-separated list of reference image URLs found during research."
    )
    theme_slug: str = Field(
        ...,
        description="Theme slug from the input theme data."
    )
    moodboard_slug: str = Field(
        ...,
        description="Generated slug for this moodboard (kebab-case)."
    )


class MoodboardElementsOutput(BaseModel):
    """
    Schema for element splitting LLM output.

    Splits a moodboard collage description into individual element
    descriptions (up to 10) for separate image generation.
    """
    moodboard_slug: str = Field(
        ...,
        description="Moodboard slug to maintain association."
    )
    elements: list[str] = Field(
        ...,
        description="List of element descriptions (up to 10). Each element "
                    "is a standalone description for individual image generation."
    )


# =============================================================================
# API Response Schemas (for future use)
# =============================================================================

class ThemeMoodboardResponse(BaseModel):
    """Response schema for moodboard data."""
    id: str
    theme_id: str
    status: str
    moodboard_slug: str | None = None
    collage_prompt: str | None = None
    collage_reference_images: list[str] | None = None
    collage_image_url: str | None = None
    element_prompts: list[str] | None = None
    element_image_urls: list[str] | None = None

    class Config:
        from_attributes = True
