from __future__ import annotations

from typing import Any

from services.impl.permission_service_impl import PermissionServiceImpl
from utils.permission_checker import PermissionResult


class PermissionController:
    def __init__(self) -> None:
        self._permission_service = PermissionServiceImpl()

    def ensure_admin_action(self, user: Any) -> PermissionResult:
        return self._permission_service.require_role(user, ["admin"])

    def ensure_activity_review(self, user: Any) -> PermissionResult:
        return self._permission_service.can_review_activity(user)

    def ensure_manage_activity(self, user: Any, activity: Any) -> PermissionResult:
        return self._permission_service.can_manage_activity(user, activity)
