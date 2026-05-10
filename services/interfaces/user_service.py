from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class UserDTO:
    user_id: int
    account: str
    name: str
    role_code: str
    role_name: str
    status: str
    phone: str
    violation_count: int
    created_at: datetime


@dataclass(frozen=True)
class PublisherApplicationDTO:
    application_id: int
    user_id: int
    account: str
    user_name: str
    organization_name: str
    responsible_person: str
    contact_info: str
    application_note: str
    status: str
    reject_reason: str
    submitted_at: datetime
    reviewed_at: datetime | None


@dataclass(frozen=True)
class UserResult:
    success: bool
    message: str
    user: UserDTO | None = None
    users: list[UserDTO] | None = None
    application: PublisherApplicationDTO | None = None
    applications: list[PublisherApplicationDTO] | None = None


class IUserService(ABC):
    @abstractmethod
    def submit_publisher_application(self, user: Any, data: dict[str, Any]) -> UserResult:
        raise NotImplementedError

    @abstractmethod
    def list_publisher_applications(self, admin_user: Any) -> UserResult:
        raise NotImplementedError

    @abstractmethod
    def approve_publisher_application(self, admin_user: Any, application_id: int) -> UserResult:
        raise NotImplementedError

    @abstractmethod
    def reject_publisher_application(self, admin_user: Any, application_id: int, reason: str) -> UserResult:
        raise NotImplementedError

    @abstractmethod
    def list_users(self, admin_user: Any, role_code: str | None = None) -> UserResult:
        raise NotImplementedError

    @abstractmethod
    def freeze_user(self, admin_user: Any, user_id: int) -> UserResult:
        raise NotImplementedError

    @abstractmethod
    def unfreeze_user(self, admin_user: Any, user_id: int) -> UserResult:
        raise NotImplementedError
