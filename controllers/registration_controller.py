from __future__ import annotations

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_registration_repository import SQLiteRegistrationRepository
from services.impl.registration_service_impl import RegistrationServiceImpl
from services.interfaces.auth_service import AuthenticatedUser
from services.interfaces.registration_service import RegistrationResult


class RegistrationController:
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
        self._registration_service = RegistrationServiceImpl(
            session=self._session,
            activity_repository=SQLiteActivityRepository(self._session),
            registration_repository=SQLiteRegistrationRepository(self._session),
        )

    def set_current_user(self, user: AuthenticatedUser | None) -> None:
        self._current_user = user

    def register_activity(self, activity_id: int) -> RegistrationResult:
        return self._registration_service.register_activity(self._get_current_user(), activity_id)

    def cancel_registration(self, registration_id: int) -> RegistrationResult:
        return self._registration_service.cancel_registration(self._get_current_user(), registration_id)

    def list_my_registrations(self) -> RegistrationResult:
        return self._registration_service.list_my_registrations(self._get_current_user())

    def list_activity_registrations(self, activity_id: int) -> RegistrationResult:
        return self._registration_service.list_activity_registrations(self._get_current_user(), activity_id)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
