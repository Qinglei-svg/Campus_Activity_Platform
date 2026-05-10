from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from utils.datetime_utils import current_datetime

if TYPE_CHECKING:
    from models.activity_model import Activity
    from models.registration_model import Registration
    from models.user_model import User


class CheckinRecord(Base):
    __tablename__ = "checkin_record"
    __table_args__ = (UniqueConstraint("registration_id", name="uq_registration_checkin"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activity.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    registration_id: Mapped[int | None] = mapped_column(ForeignKey("registration.id"), nullable=True, index=True)
    checkin_method: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="checked_in", nullable=False)
    checkin_time: Mapped[datetime] = mapped_column(DateTime, default=current_datetime, nullable=False)
    location_info: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    operator_type: Mapped[str] = mapped_column(String(40), default="user", nullable=False)
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True, index=True)
    correction_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)

    activity: Mapped[Activity] = relationship("Activity", back_populates="checkin_records")
    user: Mapped[User] = relationship("User", back_populates="checkin_records", foreign_keys=[user_id])
    operator: Mapped[User | None] = relationship("User", foreign_keys=[operator_id])
    registration: Mapped[Registration | None] = relationship("Registration", back_populates="checkin_record")
