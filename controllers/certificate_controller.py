from __future__ import annotations

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_certificate_repository import SQLiteCertificateRepository
from repositories.sqlite.sqlite_checkin_repository import SQLiteCheckinRepository
from services.impl.certificate_service_impl import CertificateServiceImpl
from services.interfaces.auth_service import AuthenticatedUser
from services.interfaces.certificate_service import CertificateResult


class CertificateController:
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
        self._certificate_service = CertificateServiceImpl(
            session=self._session,
            activity_repository=SQLiteActivityRepository(self._session),
            checkin_repository=SQLiteCheckinRepository(self._session),
            certificate_repository=SQLiteCertificateRepository(self._session),
        )

    def generate_certificate(self, activity_id: int) -> CertificateResult:
        return self._certificate_service.generate_certificate(self._get_current_user(), activity_id)

    def list_my_certificates(self) -> CertificateResult:
        return self._certificate_service.list_my_certificates(self._get_current_user())

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
