from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quest_type: Mapped[str] = mapped_column(String(64), default="repeated", nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    reward: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    schedule_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    schedule_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    progress_entries = relationship("UserProgress", back_populates="quest", lazy="raise")
