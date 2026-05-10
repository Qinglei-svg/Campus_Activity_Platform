from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from utils.datetime_utils import current_datetime

if TYPE_CHECKING:
    from models.user_model import User


class ReportAppeal(Base):
    __tablename__ = "report_appeal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submitter_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_file: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    result: Mapped[str] = mapped_column(Text, default="", nullable=False)
    handler_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=current_datetime, nullable=False)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    submitter: Mapped[User] = relationship(
        "User",
        back_populates="submitted_reports",
        foreign_keys=[submitter_id],
    )
    handler: Mapped[User | None] = relationship(
        "User",
        back_populates="handled_reports",
        foreign_keys=[handler_id],
    )
