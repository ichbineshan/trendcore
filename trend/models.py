"""
Theme Trend Model for Collection DNA.

Stores trend analysis data for themes:
- category_trends: Category-level design specs from category_trends workflow
- trend_spotting: Market validation from trend_spotting workflow (Google Trends + Ahrefs)
"""

import uuid6
from sqlalchemy import Column, String, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from utils.sqlalchemy import Base, EpochTimestampMixin


class ThemeTrend(Base, EpochTimestampMixin):
    """
    Model for storing trend analysis data for themes.

    Each theme can have one ThemeTrend record containing:
    - category_trends: JSONB with category-level design specifications
    - trend_spotting: JSONB with market validation data

    Status flow:
    - pending: Record created, workflows not started
    - category_trends_done: category_trends workflow completed
    - completed: Both workflows completed
    - failed: One or both workflows failed

    Attributes:
        id: UUID7 primary key
        theme_id: Foreign key to Theme

        category_trends: JSONB containing category-level design specs
            Structure: {
                "categories": [
                    {
                        "name": str,
                        "theme_slug": str,
                        "gender": str,
                        "age_range": str,
                        "category_static_spec": {...},
                        "category_visual_analysis": {...}
                    }
                ]
            }

        trend_spotting: JSONB containing market validation data
            Structure: {
                "season": str,
                "trends": [
                    {
                        "trend_name": str,
                        "concept": str,
                        "focus_items": list[str],
                        "key_takeaways": list[str],
                        "mood": str,
                        "market_validation": list[str],  # Google Trends
                        "commercial_validation": {...}   # Ahrefs
                    }
                ]
            }

        status: Workflow status - 'pending', 'category_trends_done', 'completed', 'failed'
    """
    __tablename__ = "theme_trends"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid6.uuid7)

    # Foreign Key to Theme
    theme_id = Column(
        UUID(as_uuid=True),
        ForeignKey("themes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One trend record per theme
    )

    # JSONB columns for trend data
    category_trends = Column(JSONB, nullable=True)
    trend_spotting = Column(JSONB, nullable=True)

    # Status tracking
    status = Column(String(50), nullable=False, default="pending")

    # Indexes
    __table_args__ = (
        Index('ix_theme_trends_theme_id', 'theme_id'),
        Index('ix_theme_trends_status', 'status'),
    )

    # Relationship
    theme = relationship("Theme", backref="theme_trend", uselist=False)

    def __repr__(self):
        return f"<ThemeTrend(id={self.id}, theme_id={self.theme_id}, status={self.status})>"
