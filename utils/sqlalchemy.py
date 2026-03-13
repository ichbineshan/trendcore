from datetime import datetime
from pytz import timezone
from sqlalchemy import Column, BigInteger
from sqlalchemy.orm import declarative_mixin, Mapped, declarative_base
from urllib.parse import urlparse, urlunparse
import time


UTC_TIME_ZONE = "UTC"


def get_current_time(time_zone: str = UTC_TIME_ZONE):
    return datetime.now(timezone(time_zone))


def async_db_url(db_url: str):
    """Convert postgres:// URL to postgresql+asyncpg://"""
    parsed_url = urlparse(db_url)
    new_scheme = "postgresql+asyncpg"
    netloc = f"{parsed_url.username}:{parsed_url.password}@{parsed_url.hostname}:{parsed_url.port}"
    updated_db_url = urlunparse((new_scheme, netloc, parsed_url.path, "", "", ""))
    return updated_db_url


@declarative_mixin
class EpochTimestampMixin:
    """
    Mixin to store timestamps as Unix epoch integers for efficient indexing and sorting.
    """

    created_at: Mapped[int] = Column(
        BigInteger, default=lambda: int(time.time()), nullable=False, index=True
    )
    updated_at: Mapped[int] = Column(
        BigInteger,
        default=lambda: int(time.time()),
        onupdate=lambda: int(time.time()),
        nullable=False,
        index=True,
    )


Base = declarative_base()
