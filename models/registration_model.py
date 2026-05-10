from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from utils.datetime_utils import current_datetime

if TYPE_CHECKING:
    from models.activity_model import Activity
    from models.checkin_model import CheckinRecord
    from models.user_model import User


class Registration(Base):
    __tablename__ = "registration"
    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uq_activity_user_registration"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activity.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="registered", nullable=False)
    waiting_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    registration_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=current_datetime, nullable=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    activity: Mapped[Activity] = relationship("Activity", back_populates="registrations")
    user: Mapped[User] = relationship("User", back_populates="registrations")
    checkin_record: Mapped[CheckinRecord | None] = relationship(
        "CheckinRecord",
        back_populates="registration",
        uselist=False,
    )
