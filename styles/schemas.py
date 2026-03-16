"""
Pydantic schemas for style generation.
"""

from enum import Enum
from typing import Optional, Any, List

from pydantic import BaseModel, Field, ConfigDict


class ReviewStatus(str, Enum):
    """Review status enum."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class StyleWebhookPayload(BaseModel):
    """Schema for style webhook payload from Naruto API."""
    model_config = ConfigDict(extra='allow')

    job_id: str = Field(..., description="External job ID from Naruto API")
    status: str = Field(..., description="Job status")
    started_at: Optional[str] = Field(None, description="Job start timestamp")
    completed_at: Optional[str] = Field(None, description="Job completion timestamp")
    progress: Optional[dict] = Field(None, description="Job progress details")
    error: Optional[str] = Field(None, description="Error message if failed")
    styles: Optional[List[dict[str, Any]]] = Field(None, description="Generated style data")


class TriggerStyleRequest(BaseModel):
    """Request schema for triggering style generation."""
    theme_id: str = Field(..., description="UUID of the theme")


class UpdateReviewRequest(BaseModel):
    """Request schema for updating review status."""
    status: ReviewStatus = Field(..., description="Review status")


class StyleResponse(BaseModel):
    """Response schema for a single style."""
    style_id: str
    theme_id: str
    external_job_id: Optional[str] = None
    external_style_id: Optional[str] = None
    status: str
    designer_review: str
    showroom_review: str
    error_message: Optional[str] = None

    # Style data
    gsm: Optional[int] = None
    cost: Optional[float] = None
    colors: Optional[List[str]] = None
    fabric: Optional[str] = None
    segment: Optional[str] = None
    garment_type: Optional[str] = None
    key_details: Optional[str] = None
    category_name: Optional[str] = None
    category_slug: Optional[str] = None
    fabric_composition: Optional[str] = None
    sheet_image: Optional[str] = None
    swatch_image: Optional[str] = None
    artwork_image: Optional[str] = None
    garment_image: Optional[str] = None
    theme_name: Optional[str] = None
    theme_slug: Optional[str] = None

    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class StyleJobResponse(BaseModel):
    """Response schema for style generation job (legacy compatibility)."""
    style_id: str
    theme_id: str
    external_job_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
