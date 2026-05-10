from __future__ import annotations

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository
from repositories.sqlite.sqlite_notification_repository import SQLiteNotificationRepository
from repositories.sqlite.sqlite_report_appeal_repository import SQLiteReportAppealRepository
from repositories.sqlite.sqlite_role_repository import SQLiteRoleRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from services.impl.notification_service_impl import NotificationServiceImpl
from services.impl.report_appeal_service_impl import ReportAppealServiceImpl
from services.interfaces.auth_service import AuthenticatedUser
from services.interfaces.report_appeal_service import ReportAppealResult


class ReportAppealController:
    def __init__(
        self,
        session: Session | None = None,
        context: ApplicationContext | None = None,
        current_user: AuthenticatedUser | None = None,
    ) -> None:
        self._owns_session = session is None
        self._session = session or SessionLocal()
        self._context = context
        self._current_user = current_user

        user_repository = SQLiteUserRepository(self._session)
        notification_service = NotificationServiceImpl(
            session=self._session,
            notification_repository=SQLiteNotificationRepository(self._session),
            user_repository=user_repository,
            role_repository=SQLiteRoleRepository(self._session),
        )
        self._report_service = ReportAppealServiceImpl(
            session=self._session,
            report_repository=SQLiteReportAppealRepository(self._session),
            user_repository=user_repository,
            activity_repository=SQLiteActivityRepository(self._session),
            audit_log_repository=SQLiteAuditLogRepository(self._session),
            notification_service=notification_service,
        )

    def submit_activity_report(self, activity_id: int, reason: str) -> ReportAppealResult:
        return self._report_service.submit_activity_report(self._get_current_user(), activity_id, reason)

    def submit_publisher_report(self, publisher_id: int, reason: str) -> ReportAppealResult:
        return self._report_service.submit_publisher_report(self._get_current_user(), publisher_id, reason)

    def submit_participant_report(self, participant_id: int, reason: str) -> ReportAppealResult:
        return self._report_service.submit_participant_report(self._get_current_user(), participant_id, reason)

    def list_my_reports(self) -> ReportAppealResult:
        return self._report_service.list_my_reports(self._get_current_user())

    def list_reports(self, status: str | None = None) -> ReportAppealResult:
        return self._report_service.list_reports(self._get_current_user(), status=status)

    def punish_report(self, report_id: int) -> ReportAppealResult:
        return self._report_service.punish_report(self._get_current_user(), report_id)

    def ignore_report(self, report_id: int, result: str = "") -> ReportAppealResult:
        return self._report_service.ignore_report(self._get_current_user(), report_id, result)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
