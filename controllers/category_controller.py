from __future__ import annotations

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from services.impl.category_service_impl import CategoryServiceImpl
from services.interfaces.auth_service import AuthenticatedUser
from services.interfaces.category_service import CategoryResult


class CategoryController:
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
        self._category_service = CategoryServiceImpl(
            session=self._session,
            category_repository=SQLiteActivityCategoryRepository(self._session),
            activity_repository=SQLiteActivityRepository(self._session),
        )

    def list_categories(self) -> CategoryResult:
        return self._category_service.list_categories(self._get_current_user())

    def create_category(self, name: str, description: str = "") -> CategoryResult:
        return self._category_service.create_category(self._get_current_user(), name, description)

    def update_category(self, category_id: int, name: str, description: str = "") -> CategoryResult:
        return self._category_service.update_category(
            self._get_current_user(),
            category_id,
            name,
            description,
        )

    def enable_category(self, category_id: int) -> CategoryResult:
        return self._category_service.enable_category(self._get_current_user(), category_id)

    def disable_category(self, category_id: int) -> CategoryResult:
        return self._category_service.disable_category(self._get_current_user(), category_id)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
