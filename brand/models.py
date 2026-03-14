import uuid6
from sqlalchemy import Column, String, Float, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from utils.sqlalchemy import Base, EpochTimestampMixin


class Brand(Base, EpochTimestampMixin):
    """
    Model for storing brand DNA and classification data from onboarding workflows.

    Stores outputs from:
    - brand_dna.py: visual_identity, design_guardrails, market_positioning,
      cultural_influences, core_values_and_voice, source_references, brand_reference_images
    - brand_classification.py: velocity, depth, strictness, notes, brand_class, reasoning

    Attributes:
        id: UUID7 primary key
        brand_name: Official brand name as extracted from brand website
        status: Workflow status - 'pending' or 'completed'
        user_request: Arbitrary nested JSON data from UI request

        # Brand DNA sections (from brand_dna.py)
        visual_identity: Color palette, overview, accessibility notes
        design_guardrails: brand_should_do and brand_should_not_do lists
        market_positioning: brand_tier, target_audience, price_range, product_categories
        cultural_influences: cultural_references, symbols, festivals, sensitivity notes
        core_values_and_voice: voice_style, heritage, story, values, design_theme
        source_references: List of URLs consulted during analysis
        brand_reference_images: List of image objects with metadata

        # Brand Classification (from brand_classification.py)
        velocity: 1-5 scale - how fast brand adopts trends
        depth: 1-5 scale - how deeply trends change products
        strictness: 1-5 scale - how tightly trends are bound by brand DNA
        classification_notes: Short descriptive note about brand characteristics
        brand_class: Classification A0-A5 (Classicist to Trend Setter)
        classification_reasoning: Explanation for the classification
    """
    __tablename__ = "brand"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid6.uuid7)
    brand_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    user_request = Column(JSONB, nullable=True)

    # Brand DNA sections (JSONB for nested structures)
    visual_identity = Column(JSONB, nullable=True)
    design_guardrails = Column(JSONB, nullable=True)
    market_positioning = Column(JSONB, nullable=True)
    cultural_influences = Column(JSONB, nullable=True)
    core_values_and_voice = Column(JSONB, nullable=True)
    source_references = Column(JSONB, nullable=True)
    brand_reference_images = Column(JSONB, nullable=True)

    # Brand Classification fields
    velocity = Column(Float, nullable=True)
    depth = Column(Float, nullable=True)
    strictness = Column(Float, nullable=True)
    classification_notes = Column(String, nullable=True)
    brand_class = Column(String, nullable=True)
    classification_reasoning = Column(String, nullable=True)

    __table_args__ = (
        Index('ix_brand_name', 'brand_name'),
        Index('ix_brand_status', 'status'),
    )

    # Relationship to collections
    collections = relationship("Collection", back_populates="brand", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Brand(id={self.id}, brand_name={self.brand_name}, status={self.status})>"

