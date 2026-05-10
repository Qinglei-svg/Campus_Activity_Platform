from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from utils.datetime_utils import current_datetime

if TYPE_CHECKING:
    from models.activity_model import Activity
    from models.audit_log_model import AuditLog
    from models.certificate_model import Certificate
    from models.checkin_model import CheckinRecord
    from models.notification_model import Notification
    from models.registration_model import Registration
    from models.report_appeal_model import ReportAppeal
    from models.review_model import Review
    from models.role_model import Role


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), nullable=False, index=True)
    account: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="enabled", nullable=False)
    phone: Mapped[str] = mapped_column(String(30), default="", nullable=False)
    violation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    frozen_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=current_datetime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=current_datetime,
        onupdate=current_datetime,
        nullable=False,
    )

    role: Mapped[Role] = relationship("Role", back_populates="users")
    activities: Mapped[list[Activity]] = relationship(
        "Activity",
        back_populates="publisher",
        foreign_keys="Activity.publisher_id",
    )
    registrations: Mapped[list[Registration]] = relationship("Registration", back_populates="user")
    checkin_records: Mapped[list[CheckinRecord]] = relationship(
        "CheckinRecord",
        back_populates="user",
        foreign_keys="CheckinRecord.user_id",
    )
    reviews: Mapped[list[Review]] = relationship("Review", back_populates="user")
    notifications: Mapped[list[Notification]] = relationship("Notification", back_populates="receiver")
    submitted_reports: Mapped[list[ReportAppeal]] = relationship(
        "ReportAppeal",
        back_populates="submitter",
        foreign_keys="ReportAppeal.submitter_id",
    )
    handled_reports: Mapped[list[ReportAppeal]] = relationship(
        "ReportAppeal",
        back_populates="handler",
        foreign_keys="ReportAppeal.handler_id",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship("AuditLog", back_populates="operator")
    certificates: Mapped[list[Certificate]] = relationship("Certificate", back_populates="user")
    publisher_applications: Mapped[list[PublisherApplication]] = relationship(
        "PublisherApplication",
        back_populates="user",
        foreign_keys="PublisherApplication.user_id",
    )
    reviewed_publisher_applications: Mapped[list[PublisherApplication]] = relationship(
        "PublisherApplication",
        back_populates="reviewer",
        foreign_keys="PublisherApplication.reviewer_id",
    )


class PublisherApplication(Base):
    __tablename__ = "publisher_application"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    organization_name: Mapped[str] = mapped_column(String(120), nullable=False)
    responsible_person: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_info: Mapped[str] = mapped_column(String(120), nullable=False)
    proof_file: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    reject_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=current_datetime, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True, index=True)

    user: Mapped[User] = relationship(
        "User",
        back_populates="publisher_applications",
        foreign_keys=[user_id],
    )
    reviewer: Mapped[User | None] = relationship(
        "User",
        back_populates="reviewed_publisher_applications",
        foreign_keys=[reviewer_id],
    )
