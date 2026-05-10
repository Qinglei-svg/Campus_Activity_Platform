from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AuditLogDTO:
    log_id: int
    operator_id: int
    operator_account: str
    operator_name: str
    operator_role_name: str
    target_type: str
    target_id: int
    action: str
    action_name: str
    result: str
    reason: str
    operated_at: datetime


@dataclass(frozen=True)
class AuditLogResult:
    success: bool
    message: str
    logs: list[AuditLogDTO] | None = None
    actions: list[tuple[str, str]] | None = None


class IAuditLogService(ABC):
    @abstractmethod
    def list_logs(
        self,
        admin_user: Any,
        action: str | None = None,
        operator_keyword: str | None = None,
    ) -> AuditLogResult:
        raise NotImplementedError

    @abstractmethod
    def list_action_options(self, admin_user: Any) -> AuditLogResult:
        raise NotImplementedError
