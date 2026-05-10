from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from utils.permission_checker import PermissionResult


class IPermissionService(ABC):
    @abstractmethod
    def require_role(self, user: Any, allowed_roles: list[str]) -> PermissionResult:
        raise NotImplementedError

    @abstractmethod
    def can_access_menu(self, user: Any, menu_name: str) -> PermissionResult:
        raise NotImplementedError

    @abstractmethod
    def can_review_activity(self, user: Any) -> PermissionResult:
        raise NotImplementedError

    @abstractmethod
    def can_manage_activity(self, user: Any, activity: Any) -> PermissionResult:
        raise NotImplementedError
