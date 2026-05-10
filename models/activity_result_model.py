from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from utils.datetime_utils import current_datetime

if TYPE_CHECKING:
    from models.activity_model import Activity


class ActivityResult(Base):
    __tablename__ = "activity_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activity.id"), nullable=False, index=True)
    news_title: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    image_files: Mapped[str] = mapped_column(Text, default="", nullable=False)
    attachment_file: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=current_datetime, nullable=False)

    activity: Mapped[Activity] = relationship("Activity", back_populates="results")
