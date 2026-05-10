from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.audit_log_model import AuditLog
from models.user_model import User
from repositories.interfaces.audit_log_repository import IAuditLogRepository


class SQLiteAuditLogRepository(IAuditLogRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, log: AuditLog) -> AuditLog:
        self._session.add(log)
        self._session.flush()
        return log

    def list_all(self) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .options(joinedload(AuditLog.operator).joinedload(User.role))
            .order_by(AuditLog.operated_at.desc())
        )
        return list(self._session.scalars(statement).all())
