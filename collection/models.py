import uuid6
from sqlalchemy import Column, String, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from utils.sqlalchemy import Base, EpochTimestampMixin


class Collection(Base, EpochTimestampMixin):
    """
    Model for storing capsule collection data.

    A brand can have multiple collections. Each collection stores
    trend data, moodboards, and other collection-specific information.

    Attributes:
        id: UUID7 primary key
        brand_id: Foreign key to Brand
        collection_name: LLM-generated collection name (e.g., "Breezy Resortwear")
        status: Workflow status - 'pending' or 'completed' or 'failed'
        user_req: Full input payload from user
        overview: LLM-generated narrative paragraph
        range_overview: LLM-generated range overview (stats + items table)
    """
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid6.uuid7)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brand.id", ondelete="CASCADE"), nullable=False)
    collection_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    user_req = Column(JSONB, nullable=True)
    overview = Column(Text, nullable=True)
    range_overview = Column(JSONB, nullable=True)

    # Relationship to brand
    brand = relationship("Brand", back_populates="collections")

    # Relationship to themes
    themes = relationship("Theme", back_populates="collection", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_collections_brand_id', 'brand_id'),
        Index('ix_collections_status', 'status'),
    )

    def __repr__(self):
        return f"<Collection(id={self.id}, collection_name={self.collection_name}, brand_id={self.brand_id})>"
