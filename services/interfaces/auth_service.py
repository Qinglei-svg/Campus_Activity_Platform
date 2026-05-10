from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    account: str
    name: str
    phone: str
    role_id: int
    role_code: str
    role_name: str
    status: str


@dataclass(frozen=True)
class AuthResult:
    success: bool
    message: str
    user: AuthenticatedUser | None = None


class IAuthService(ABC):
    @abstractmethod
    def login(self, account: str, password: str) -> AuthResult:
        raise NotImplementedError

    @abstractmethod
    def register(self, account: str, name: str, password: str, phone: str) -> AuthResult:
        raise NotImplementedError

    @abstractmethod
    def change_password(self, user_id: int, old_password: str, new_password: str) -> AuthResult:
        raise NotImplementedError
