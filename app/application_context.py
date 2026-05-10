from __future__ import annotations

from dataclasses import dataclass

from services.interfaces.auth_service import AuthenticatedUser
from utils.permission_checker import PermissionChecker


@dataclass
class ApplicationContext:
    current_user: AuthenticatedUser | None = None

    def set_current_user(self, user: AuthenticatedUser) -> None:
        self.current_user = user

    def clear_current_user(self) -> None:
        self.current_user = None

    def get_current_user(self) -> AuthenticatedUser | None:
        return self.current_user

    def get_current_menus(self) -> list[str]:
        return PermissionChecker.get_allowed_menus(self.current_user)
