"""
Theme Model for Collection DNA.

Stores generated theme data for collections including:
- Basic theme info (name, description, mood)
- Color direction with Pantone/Coloro codes
- Material and silhouette direction
- Micro trends
- UI-friendly suggestions (fabric, trim, artwork)
- Moodboard data
"""

import uuid6
from sqlalchemy import Column, String, Text, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from utils.sqlalchemy import Base, EpochTimestampMixin
from enum import Enum as PyEnum


class ReviewStatus(str, PyEnum):
    """Review status for themes."""
    approved = "approved"
    rejected = "rejected"



class Theme(Base, EpochTimestampMixin):
    """
    Model for storing generated theme data for collections.

    A collection can have multiple themes. Each theme stores
    design direction, color palettes, material suggestions, and moodboard data.

    Attributes:
        id: UUID7 primary key
        collection_id: Foreign key to Collection

        # Basic Info
        theme_name: LLM-generated theme name (e.g., "Urban Nomad")
        theme_slug: Kebab-case identifier (e.g., "urban-nomad")
        season_title: Season with year (e.g., "Summer Spring 2026")
        main_concept: Core concept paragraph
        one_line_summary: Single sentence summary
        mood_tags: Comma-separated mood adjectives
        design_keywords: List of design intent keywords
        aesthetic_labels: Short aesthetic flavor labels
        is_aligned_to_brand_dna: Whether theme aligns with brand DNA

        # Trend Narrative
        key_story_points: Multi-paragraph narrative
        lifestyle_context_notes: Lifestyle context description
        gender_or_inclusivity_notes: Gender/inclusivity notes

        # Color Direction
        primary_colors, accent_colors, neutral_colors: Color lists
        palette_notes: Usage intent notes
        palette: Short palette sentence
        meaningful_color_associations: Color associations
        pantone_codes: Pantone TCX codes from WGSN
        coloro_codes: Coloro codes from WGSN

        # Material & Silhouette Direction
        fabric_notes, trim_keywords, print_keywords: Material keywords
        important_fabrics, important_silhouettes: Key materials
        key_silhouettes, key_trend_fabrics: Summary strings
        print_usage_guidelines: Print usage notes

        # Micro Trends
        print_placement_trends, wash_and_finish_trends, etc.

        # UI Suggestions
        fabric_suggestions, trim_suggestions, artwork_suggestions

        # Moodboard
        moodboard_description: Description for image generation
        moodboard_image_url: Generated moodboard image URL

        # Metadata
        generation_input: Original theme requirement from user
        references: Source references
        status: Workflow status - 'pending', 'completed', 'failed'
    """
    __tablename__ = "themes"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid6.uuid7)

    # Foreign Key
    collection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
    )

    # =========================================================================
    # Basic Info
    # =========================================================================
    theme_name = Column(String(255), nullable=False)
    theme_slug = Column(String(255), nullable=False)
    season_title = Column(String(100), nullable=True)
    main_concept = Column(Text, nullable=True)
    one_line_summary = Column(String(500), nullable=True)
    mood_tags = Column(String(500), nullable=True)  # Comma-separated
    design_keywords = Column(JSONB, nullable=True)
    aesthetic_labels = Column(JSONB, nullable=True)
    is_aligned_to_brand_dna = Column(Boolean, nullable=True, default=True)

    # =========================================================================
    # Trend Narrative
    # =========================================================================
    key_story_points = Column(Text, nullable=True)
    lifestyle_context_notes = Column(Text, nullable=True)
    gender_or_inclusivity_notes = Column(Text, nullable=True)

    # =========================================================================
    # Color Direction
    # =========================================================================
    primary_colors = Column(JSONB, nullable=True)
    accent_colors = Column(JSONB, nullable=True)
    neutral_colors = Column(JSONB, nullable=True)
    palette_notes = Column(JSONB, nullable=True)
    palette = Column(String(500), nullable=True)
    meaningful_color_associations = Column(JSONB, nullable=True)

    # Pantone/Coloro codes from MCP (WGSN data)
    pantone_codes = Column(JSONB, nullable=True)  # ["18-1140 TCX", ...]
    coloro_codes = Column(JSONB, nullable=True)  # ["098-59-30", ...]

    # =========================================================================
    # Material & Silhouette Direction
    # =========================================================================
    fabric_notes = Column(JSONB, nullable=True)
    trim_keywords = Column(JSONB, nullable=True)
    print_keywords = Column(JSONB, nullable=True)
    important_fabrics = Column(JSONB, nullable=True)
    important_silhouettes = Column(JSONB, nullable=True)
    key_silhouettes = Column(String(500), nullable=True)
    key_trend_fabrics = Column(String(500), nullable=True)
    print_usage_guidelines = Column(JSONB, nullable=True)

    # =========================================================================
    # Micro Trends
    # =========================================================================
    print_placement_trends = Column(JSONB, nullable=True)
    wash_and_finish_trends = Column(JSONB, nullable=True)
    graphic_and_icon_trends = Column(JSONB, nullable=True)
    typography_micro_trends = Column(JSONB, nullable=True)
    fit_and_proportion_trends = Column(JSONB, nullable=True)
    other_micro_trend_signals = Column(JSONB, nullable=True)
    construction_detail_trends = Column(JSONB, nullable=True)
    accessory_and_styling_trends = Column(JSONB, nullable=True)

    # =========================================================================
    # UI-Friendly Suggestions (Simple lists for frontend display)
    # =========================================================================
    fabric_suggestions = Column(JSONB, nullable=True)  # ["Organic Cotton Twill", ...]
    trim_suggestions = Column(JSONB, nullable=True)  # ["Wooden Buttons", ...]
    artwork_suggestions = Column(JSONB, nullable=True)  # ["Block Print Motif", ...]



    # =========================================================================
    # Generation Metadata
    # =========================================================================
    generation_input = Column(JSONB, nullable=True)  # Original theme requirement
    references = Column(JSONB, nullable=True)  # Source references

    # =========================================================================
    # Status
    # =========================================================================
    status = Column(String(50), nullable=False, default="pending")

    # =========================================================================
    # Review Status
    # =========================================================================
    review_status = Column(String(20), nullable=True, default=None)  # null = not reviewed
    review_notes = Column(Text, nullable=True)

    # =========================================================================
    # Indexes
    # =========================================================================
    __table_args__ = (
        Index('ix_themes_collection_id', 'collection_id'),
        Index('ix_themes_status', 'status'),
        Index('ix_themes_theme_slug', 'theme_slug'),
    )

    # =========================================================================
    # Relationships
    # =========================================================================
    collection = relationship("Collection", back_populates="themes")

    def __repr__(self):
        return f"<Theme(id={self.id}, theme_name={self.theme_name}, collection_id={self.collection_id})>"
