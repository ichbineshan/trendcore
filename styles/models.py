"""
ThemeStyle Model for Collection DNA.

Stores individual style records for themes.
"""

import uuid6
from sqlalchemy import Column, String, Text, Index, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from utils.sqlalchemy import Base, EpochTimestampMixin


class ThemeStyle(Base, EpochTimestampMixin):
    """
    Model for storing individual style records for themes.

    Each row represents one style from Naruto API response.
    Multiple styles can belong to the same theme and external_job_id.

    Attributes:
        id: UUID7 primary key (style_id)
        theme_id: Foreign key to themes.id
        external_job_id: Job ID returned by Naruto API (shared across styles from same job)
        external_style_id: Style ID from Naruto API response
        status: Current status (pending, processing, completed, failed)
        designer_review: Designer review status (pending, approved, rejected)
        showroom_review: Showroom review status (pending, approved, rejected)
        error_message: Error message if job failed

        Style data columns from Naruto API:
        gsm: Fabric weight (grams per square meter)
        cost: Style cost
        colors: Array of color names
        fabric: Fabric type
        segment: Market segment
        garment_type: Type of garment
        key_details: Key design details
        category_name: Category display name
        category_slug: Category URL slug
        fabric_composition: Fabric material composition
        sheet_image: Sheet image URL
        swatch_image: Swatch image URL
        artwork_image: Artwork image URL
        garment_image: Garment image URL
        theme_name: Theme name from Naruto
        theme_slug: Theme slug from Naruto
    """
    __tablename__ = "theme_styles"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid6.uuid7)
    theme_id = Column(
        UUID(as_uuid=True),
        ForeignKey("themes.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_job_id = Column(String, nullable=True)
    external_style_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    designer_review = Column(String, nullable=False, default="pending")
    showroom_review = Column(String, nullable=False, default="pending")
    error_message = Column(Text, nullable=True)

    # Style data columns
    gsm = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    colors = Column(ARRAY(String), nullable=True)
    fabric = Column(String, nullable=True)
    segment = Column(String, nullable=True)
    garment_type = Column(String, nullable=True)
    key_details = Column(Text, nullable=True)
    category_name = Column(String, nullable=True)
    category_slug = Column(String, nullable=True)
    fabric_composition = Column(String, nullable=True)
    sheet_image = Column(String, nullable=True)
    swatch_image = Column(String, nullable=True)
    artwork_image = Column(String, nullable=True)
    garment_image = Column(String, nullable=True)
    theme_name = Column(String, nullable=True)
    theme_slug = Column(String, nullable=True)

    __table_args__ = (
        Index('ix_theme_styles_theme_id', 'theme_id'),
        Index('ix_theme_styles_status', 'status'),
        Index('ix_theme_styles_external_job_id', 'external_job_id'),
        Index('ix_theme_styles_designer_review', 'designer_review'),
        Index('ix_theme_styles_showroom_review', 'showroom_review'),
    )

    def __repr__(self):
        return f"<ThemeStyle(id={self.id}, theme_id={self.theme_id}, status={self.status})>"
