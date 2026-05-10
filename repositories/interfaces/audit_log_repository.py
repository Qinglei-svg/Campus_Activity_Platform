from __future__ import annotations

from abc import ABC, abstractmethod

from models.audit_log_model import AuditLog


class IAuditLogRepository(ABC):
    @abstractmethod
    def save(self, log: AuditLog) -> AuditLog:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[AuditLog]:
        raise NotImplementedError
