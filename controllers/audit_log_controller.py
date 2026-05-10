from __future__ import annotations

from sqlalchemy.orm import Session

from app.application_context import ApplicationContext
from database.db import SessionLocal
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository
from services.impl.audit_log_service_impl import AuditLogServiceImpl
from services.interfaces.audit_log_service import AuditLogResult
from services.interfaces.auth_service import AuthenticatedUser


class AuditLogController:
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
        self._audit_log_service = AuditLogServiceImpl(
            audit_log_repository=SQLiteAuditLogRepository(self._session)
        )

    def list_logs(self, action: str | None = None, operator_keyword: str | None = None) -> AuditLogResult:
        return self._audit_log_service.list_logs(
            self._get_current_user(),
            action=action,
            operator_keyword=operator_keyword,
        )

    def list_action_options(self) -> AuditLogResult:
        return self._audit_log_service.list_action_options(self._get_current_user())

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _get_current_user(self) -> AuthenticatedUser | None:
        if self._context is not None:
            return self._context.get_current_user()
        return self._current_user
