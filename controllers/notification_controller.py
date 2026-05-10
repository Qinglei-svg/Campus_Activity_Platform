from __future__ import annotations

from sqlalchemy.orm import Session

from database.db import SessionLocal
from repositories.sqlite.sqlite_notification_repository import SQLiteNotificationRepository
from repositories.sqlite.sqlite_role_repository import SQLiteRoleRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from services.impl.notification_service_impl import NotificationServiceImpl
from services.interfaces.notification_service import NotificationResult


class NotificationController:
    def __init__(self, session: Session | None = None) -> None:
        self._owns_session = session is None
        self._session = session or SessionLocal()
        self._notification_service = NotificationServiceImpl(
            session=self._session,
            notification_repository=SQLiteNotificationRepository(self._session),
            user_repository=SQLiteUserRepository(self._session),
            role_repository=SQLiteRoleRepository(self._session),
        )

    def send_to_user(self, user_id: int, title: str, content: str, type: str) -> NotificationResult:
        return self._notification_service.send_to_user(user_id, title, content, type)

    def list_user_notifications(self, user_id: int) -> NotificationResult:
        return self._notification_service.list_user_notifications(user_id)

    def mark_as_read(self, notification_id: int) -> NotificationResult:
        return self._notification_service.mark_as_read(notification_id)

    def delete_notification(self, notification_id: int) -> NotificationResult:
        return self._notification_service.delete_notification(notification_id)

    def send_to_role(self, role_code: str, title: str, content: str, type: str) -> NotificationResult:
        return self._notification_service.send_to_role(role_code, title, content, type)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()
