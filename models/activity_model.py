from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from utils.datetime_utils import current_datetime

if TYPE_CHECKING:
    from models.activity_result_model import ActivityResult
    from models.certificate_model import Certificate
    from models.checkin_model import CheckinRecord
    from models.registration_model import Registration
    from models.review_model import Review
    from models.user_model import User


class ActivityCategory(Base):
    __tablename__ = "activity_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=current_datetime, nullable=False)

    activities: Mapped[list[Activity]] = relationship("Activity", back_populates="category")


class Activity(Base):
    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    publisher_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("activity_category.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    cover_image: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    signup_start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    signup_end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    signup_condition: Mapped[str] = mapped_column(Text, default="", nullable=False)
    need_signup_audit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    credit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    volunteer_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    checkin_code: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    checkin_method: Mapped[str] = mapped_column(String(40), default="code", nullable=False)
    checkin_open: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reject_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=current_datetime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=current_datetime,
        onupdate=current_datetime,
        nullable=False,
    )

    publisher: Mapped[User] = relationship(
        "User",
        back_populates="activities",
        foreign_keys=[publisher_id],
    )
    category: Mapped[ActivityCategory] = relationship("ActivityCategory", back_populates="activities")
    registrations: Mapped[list[Registration]] = relationship("Registration", back_populates="activity")
    checkin_records: Mapped[list[CheckinRecord]] = relationship("CheckinRecord", back_populates="activity")
    reviews: Mapped[list[Review]] = relationship("Review", back_populates="activity")
    certificates: Mapped[list[Certificate]] = relationship("Certificate", back_populates="activity")
    results: Mapped[list[ActivityResult]] = relationship("ActivityResult", back_populates="activity")
