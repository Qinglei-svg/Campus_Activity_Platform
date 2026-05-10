from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from services.interfaces.activity_service import ActivityResult


class IAuditService(ABC):
    @abstractmethod
    def list_pending_activities(self, current_user: Any) -> ActivityResult:
        raise NotImplementedError

    @abstractmethod
    def approve_activity(self, current_user: Any, activity_id: int) -> ActivityResult:
        raise NotImplementedError

    @abstractmethod
    def reject_activity(self, current_user: Any, activity_id: int, reason: str) -> ActivityResult:
        raise NotImplementedError
