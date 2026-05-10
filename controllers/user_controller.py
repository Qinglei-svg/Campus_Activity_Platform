from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository
from repositories.sqlite.sqlite_notification_repository import SQLiteNotificationRepository
from repositories.sqlite.sqlite_role_repository import SQLiteRoleRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from services.impl.notification_service_impl import NotificationServiceImpl
from services.impl.user_service_impl import UserServiceImpl
from services.interfaces.auth_service import AuthenticatedUser
from services.interfaces.user_service import UserResult


class UserController:
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
        role_repository = SQLiteRoleRepository(self._session)
        notification_service = NotificationServiceImpl(
            session=self._session,
            notification_repository=SQLiteNotificationRepository(self._session),
            user_repository=user_repository,
            role_repository=role_repository,
        )
        self._user_service = UserServiceImpl(
            session=self._session,
            user_repository=user_repository,
            role_repository=role_repository,
            audit_log_repository=SQLiteAuditLogRepository(self._session),
            notification_service=notification_service,
        )

    def submit_publisher_application(self, data: dict[str, Any]) -> UserResult:
        return self._user_service.submit_publisher_application(self._get_current_user(), data)

    def list_publisher_applications(self) -> UserResult:
        return self._user_service.list_publisher_applications(self._get_current_user())

    def approve_publisher_application(self, application_id: int) -> UserResult:
        return self._user_service.approve_publisher_application(self._get_current_user(), application_id)

    def reject_publisher_application(self, application_id: int, reason: str) -> UserResult:
        return self._user_service.reject_publisher_application(self._get_current_user(), application_id, reason)

    def list_users(self, role_code: str | None = None) -> UserResult:
        return self._user_service.list_users(self._get_current_user(), role_code=role_code)

    def freeze_user(self, user_id: int) -> UserResult:
        return self._user_service.freeze_user(self._get_current_user(), user_id)

    def unfreeze_user(self, user_id: int) -> UserResult:
        return self._user_service.unfreeze_user(self._get_current_user(), user_id)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
