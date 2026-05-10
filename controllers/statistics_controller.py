from __future__ import annotations

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_certificate_repository import SQLiteCertificateRepository
from repositories.sqlite.sqlite_checkin_repository import SQLiteCheckinRepository
from repositories.sqlite.sqlite_registration_repository import SQLiteRegistrationRepository
from repositories.sqlite.sqlite_review_repository import SQLiteReviewRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from services.impl.statistics_service_impl import StatisticsServiceImpl
from services.interfaces.auth_service import AuthenticatedUser
from services.interfaces.statistics_service import StatisticsResult


class StatisticsController:
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
        self._statistics_service = StatisticsServiceImpl(
            user_repository=SQLiteUserRepository(self._session),
            activity_repository=SQLiteActivityRepository(self._session),
            category_repository=SQLiteActivityCategoryRepository(self._session),
            registration_repository=SQLiteRegistrationRepository(self._session),
            checkin_repository=SQLiteCheckinRepository(self._session),
            review_repository=SQLiteReviewRepository(self._session),
            certificate_repository=SQLiteCertificateRepository(self._session),
        )

    def get_admin_statistics(self) -> StatisticsResult:
        return self._statistics_service.get_admin_statistics(self._get_current_user())

    def get_publisher_statistics(self) -> StatisticsResult:
        return self._statistics_service.get_publisher_statistics(self._get_current_user())

    def get_participant_statistics(self) -> StatisticsResult:
        return self._statistics_service.get_participant_statistics(self._get_current_user())

    def list_publisher_calendar_events(self) -> StatisticsResult:
        return self._statistics_service.list_publisher_calendar_events(self._get_current_user())

    def list_participant_calendar_events(self) -> StatisticsResult:
        return self._statistics_service.list_participant_calendar_events(self._get_current_user())

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
