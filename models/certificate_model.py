from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from utils.datetime_utils import current_datetime

if TYPE_CHECKING:
    from models.activity_model import Activity
    from models.user_model import User


class Certificate(Base):
    __tablename__ = "certificate"
    __table_args__ = (UniqueConstraint("certificate_no", name="uq_certificate_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activity.id"), nullable=False, index=True)
    certificate_no: Mapped[str] = mapped_column(String(120), nullable=False)
    certificate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=current_datetime, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="certificates")
    activity: Mapped[Activity] = relationship("Activity", back_populates="certificates")
