from enum import Enum

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Index,
    UUID,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from utils.sqlalchemy import Base, EpochTimestampMixin


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Thread(Base, EpochTimestampMixin):
    __tablename__ = "thread"

    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String)
    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)
    meta = Column(JSON, default={})
    last_message_id = Column(UUID(as_uuid=True), nullable=True)
    user_email = Column(String, nullable=True, index=True)

    messages = relationship(
        "ThreadMessage", back_populates="thread", cascade="all, delete-orphan"
    )
    tasks = relationship(
        "Task", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        Index(
            'ix_thread_user_org_updated',
            'user_id', 'org_id', 'updated_at'
        ),
    )


class ThreadMessage(EpochTimestampMixin, Base):
    __tablename__ = "thread_message"

    id = Column(UUID(as_uuid=True), primary_key=True)
    thread_uuid = Column(UUID(as_uuid=True), ForeignKey("thread.id", ondelete="CASCADE"), index=True)
    parent_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("thread_message.id", ondelete="CASCADE"),
        nullable=True,
    )
    content = Column(JSONB, nullable=True)
    role = Column(SQLEnum(Role))
    prompt_details = Column(JSONB, default={})
    images = Column(JSONB, default=[], nullable=True)
    user_query = Column(String, nullable=True)
    meta_data = Column(JSONB, nullable=True, default={})

    thread = relationship("Thread", back_populates="messages")


class Task(EpochTimestampMixin, Base):
    __tablename__ = "task"

    id = Column(UUID(as_uuid=True), primary_key=True)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("thread.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")
