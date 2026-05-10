from __future__ import annotations

from typing import Any

from services.interfaces.permission_service import IPermissionService
from utils.permission_checker import (
    PERMISSION_DENIED_MESSAGE,
    PermissionChecker,
    PermissionResult,
    ROLE_CODE_ADMIN,
)


class PermissionServiceImpl(IPermissionService):
    def require_role(self, user: Any, allowed_roles: list[str]) -> PermissionResult:
        return PermissionChecker.require_role(user, allowed_roles)

    def can_access_menu(self, user: Any, menu_name: str) -> PermissionResult:
        return PermissionChecker.can_access_menu(user, menu_name)

    def can_review_activity(self, user: Any) -> PermissionResult:
        return PermissionChecker.require_role(user, [ROLE_CODE_ADMIN])

    def can_manage_activity(self, user: Any, activity: Any) -> PermissionResult:
        if PermissionChecker.can_manage_activity(user, activity):
            return PermissionResult(True, "权限检查通过")
        return PermissionResult(False, PERMISSION_DENIED_MESSAGE)
