from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from utils.datetime_utils import current_datetime

if TYPE_CHECKING:
    from models.activity_model import Activity
    from models.user_model import User


class Review(Base):
    __tablename__ = "review"
    __table_args__ = (UniqueConstraint("activity_id", "user_id", name="uq_activity_user_review"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activity.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    content_score: Mapped[float] = mapped_column(Float, nullable=False)
    organization_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="visible", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=current_datetime, nullable=False)

    activity: Mapped[Activity] = relationship("Activity", back_populates="reviews")
    user: Mapped[User] = relationship("User", back_populates="reviews")
