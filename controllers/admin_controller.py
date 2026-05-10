from __future__ import annotations

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository
from repositories.sqlite.sqlite_notification_repository import SQLiteNotificationRepository
from repositories.sqlite.sqlite_role_repository import SQLiteRoleRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from services.impl.audit_service_impl import AuditServiceImpl
from services.impl.notification_service_impl import NotificationServiceImpl
from services.interfaces.activity_service import ActivityResult
from services.interfaces.auth_service import AuthenticatedUser


class AdminController:
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
        self._audit_service = AuditServiceImpl(
            session=self._session,
            activity_repository=SQLiteActivityRepository(self._session),
            audit_log_repository=SQLiteAuditLogRepository(self._session),
            notification_service=notification_service,
        )

    def set_current_user(self, user: AuthenticatedUser | None) -> None:
        self._current_user = user

    def list_pending_activities(self) -> ActivityResult:
        return self._audit_service.list_pending_activities(self._get_current_user())

    def approve_activity(self, activity_id: int) -> ActivityResult:
        return self._audit_service.approve_activity(self._get_current_user(), activity_id)

    def reject_activity(self, activity_id: int, reason: str) -> ActivityResult:
        return self._audit_service.reject_activity(self._get_current_user(), activity_id, reason)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
