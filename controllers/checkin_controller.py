from __future__ import annotations

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository
from repositories.sqlite.sqlite_checkin_repository import SQLiteCheckinRepository
from repositories.sqlite.sqlite_notification_repository import SQLiteNotificationRepository
from repositories.sqlite.sqlite_registration_repository import SQLiteRegistrationRepository
from repositories.sqlite.sqlite_role_repository import SQLiteRoleRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from services.impl.checkin_service_impl import CheckinServiceImpl
from services.impl.notification_service_impl import NotificationServiceImpl
from services.interfaces.auth_service import AuthenticatedUser
from services.interfaces.checkin_service import CheckinResult


class CheckinController:
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
        notification_service = NotificationServiceImpl(
            session=self._session,
            notification_repository=SQLiteNotificationRepository(self._session),
            user_repository=SQLiteUserRepository(self._session),
            role_repository=SQLiteRoleRepository(self._session),
        )
        self._checkin_service = CheckinServiceImpl(
            session=self._session,
            activity_repository=SQLiteActivityRepository(self._session),
            registration_repository=SQLiteRegistrationRepository(self._session),
            checkin_repository=SQLiteCheckinRepository(self._session),
            audit_log_repository=SQLiteAuditLogRepository(self._session),
            notification_service=notification_service,
        )

    def enable_checkin(self, activity_id: int, method: str, code: str) -> CheckinResult:
        return self._checkin_service.enable_checkin(self._get_current_user(), activity_id, method, code)

    def participant_checkin(self, activity_id: int, code: str) -> CheckinResult:
        return self._checkin_service.participant_checkin(self._get_current_user(), activity_id, code)

    def list_activity_checkins(self, activity_id: int) -> CheckinResult:
        return self._checkin_service.list_activity_checkins(self._get_current_user(), activity_id)

    def list_my_checkins(self) -> CheckinResult:
        return self._checkin_service.list_my_checkins(self._get_current_user())

    def correct_checkin(self, registration_id: int, status: str, reason: str) -> CheckinResult:
        return self._checkin_service.correct_checkin(self._get_current_user(), registration_id, status, reason)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
