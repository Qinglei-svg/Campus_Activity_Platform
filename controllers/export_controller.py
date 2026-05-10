from __future__ import annotations

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_checkin_repository import SQLiteCheckinRepository
from repositories.sqlite.sqlite_registration_repository import SQLiteRegistrationRepository
from services.impl.export_service_impl import ExportServiceImpl
from services.interfaces.auth_service import AuthenticatedUser
from services.interfaces.export_service import ExportResult


class ExportController:
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
        self._export_service = ExportServiceImpl(
            activity_repository=SQLiteActivityRepository(self._session),
            registration_repository=SQLiteRegistrationRepository(self._session),
            checkin_repository=SQLiteCheckinRepository(self._session),
        )

    def export_activity_registration_excel(self, activity_id: int) -> ExportResult:
        return self._export_service.export_activity_registration_excel(self._get_current_user(), activity_id)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
