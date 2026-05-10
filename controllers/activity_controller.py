from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_notification_repository import SQLiteNotificationRepository
from repositories.sqlite.sqlite_role_repository import SQLiteRoleRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from services.impl.activity_service_impl import ActivityServiceImpl
from services.impl.notification_service_impl import NotificationServiceImpl
from services.interfaces.activity_service import ActivityResult
from services.interfaces.auth_service import AuthenticatedUser


class ActivityController:
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
        self._activity_service = ActivityServiceImpl(
            activity_repository=SQLiteActivityRepository(self._session),
            category_repository=SQLiteActivityCategoryRepository(self._session),
            session=self._session,
            notification_service=notification_service,
        )

    def set_current_user(self, user: AuthenticatedUser | None) -> None:
        self._current_user = user

    def list_online_activities(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
    ) -> ActivityResult:
        return self._activity_service.list_online_activities(
            {"keyword": keyword, "category_id": category_id}
        )

    def get_activity_detail(self, activity_id: int, current_user: Any | None = None) -> ActivityResult:
        return self._activity_service.get_activity_detail(
            activity_id,
            current_user=current_user or self._get_current_user(),
        )

    def list_categories(self) -> ActivityResult:
        return self._activity_service.list_categories()

    def create_draft(self, data: dict[str, Any]) -> ActivityResult:
        return self._activity_service.create_draft(self._get_current_user(), data)

    def update_activity(self, activity_id: int, data: dict[str, Any]) -> ActivityResult:
        return self._activity_service.update_activity(self._get_current_user(), activity_id, data)

    def submit_activity(self, activity_id: int) -> ActivityResult:
        return self._activity_service.submit_activity(self._get_current_user(), activity_id)

    def list_my_activities(self, status: str | None = None) -> ActivityResult:
        return self._activity_service.list_my_activities(self._get_current_user(), status=status)

    def get_my_activity_detail(self, activity_id: int) -> ActivityResult:
        return self._activity_service.get_my_activity_detail(self._get_current_user(), activity_id)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
