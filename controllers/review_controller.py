from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository
from repositories.sqlite.sqlite_checkin_repository import SQLiteCheckinRepository
from repositories.sqlite.sqlite_review_repository import SQLiteReviewRepository
from services.impl.review_service_impl import ReviewServiceImpl
from services.interfaces.auth_service import AuthenticatedUser
from services.interfaces.review_service import ReviewResult


class ReviewController:
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
        self._review_service = ReviewServiceImpl(
            session=self._session,
            activity_repository=SQLiteActivityRepository(self._session),
            checkin_repository=SQLiteCheckinRepository(self._session),
            review_repository=SQLiteReviewRepository(self._session),
            audit_log_repository=SQLiteAuditLogRepository(self._session),
        )

    def submit_review(self, activity_id: int, data: dict[str, Any]) -> ReviewResult:
        return self._review_service.submit_review(self._get_current_user(), activity_id, data)

    def list_activity_reviews(self, activity_id: int) -> ReviewResult:
        return self._review_service.list_activity_reviews(self._get_current_user(), activity_id)

    def list_admin_reviews(self) -> ReviewResult:
        return self._review_service.list_admin_reviews(self._get_current_user())

    def delete_review(self, review_id: int, reason: str = "管理员删除违规评价") -> ReviewResult:
        return self._review_service.delete_review(self._get_current_user(), review_id, reason)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
