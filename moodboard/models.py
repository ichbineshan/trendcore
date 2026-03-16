"""
ThemeMoodboard Model for Collection DNA.

Stores moodboard data for themes including:
- Collage prompt (detailed description for image generation)
- Reference images found during research
- Element prompts (split from collage for individual image generation)
- Generated image URLs
"""

import uuid6
from sqlalchemy import Column, String, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from utils.sqlalchemy import Base, EpochTimestampMixin


class ThemeMoodboard(Base, EpochTimestampMixin):
    """
    Model for storing moodboard data for themes.

    Each theme has one moodboard. The workflow generates:
    1. A detailed collage prompt (for collage image generation)
    2. Element prompts (for individual image generation)

    Status transitions:
    - pending -> generating_collage -> generating_elements -> completed
    - Any state -> failed (on error)

    Attributes:
        id: UUID7 primary key
        theme_id: Foreign key to Theme (one-to-one)
        status: Workflow status
        moodboard_slug: Identifier for the moodboard
        collage_prompt: Detailed description for collage image generation
        collage_reference_images: URLs found during web search research
        collage_image_url: Generated collage image URL
        element_prompts: List of element descriptions (split from collage)
        element_image_urls: List of generated element image URLs
    """
    __tablename__ = "theme_moodboards"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid6.uuid7)

    # Foreign Key (one-to-one with Theme)
    theme_id = Column(
        UUID(as_uuid=True),
        ForeignKey("themes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Status
    status = Column(String(50), nullable=False, default="pending")

    # Moodboard Identity
    moodboard_slug = Column(String(255), nullable=True)

    # Collage Generation
    collage_prompt = Column(Text, nullable=True)
    collage_reference_images = Column(JSONB, nullable=True)  # list[str] - URLs
    collage_image_url = Column(String(1024), nullable=True)

    # Element Generation
    element_prompts = Column(JSONB, nullable=True)  # list[str] - up to 10 elements
    element_image_urls = Column(JSONB, nullable=True)  # list[str] - generated URLs

    # Indexes
    __table_args__ = (
        Index('ix_theme_moodboards_theme_id', 'theme_id'),
        Index('ix_theme_moodboards_status', 'status'),
    )

    # Relationships
    theme = relationship("Theme", backref="moodboard", uselist=False)

    def __repr__(self):
        return f"<ThemeMoodboard(id={self.id}, theme_id={self.theme_id}, status={self.status})>"
