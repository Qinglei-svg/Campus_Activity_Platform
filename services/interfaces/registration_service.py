from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RegistrationDTO:
    registration_id: int
    activity_id: int
    activity_title: str
    category_name: str
    publisher_name: str
    user_id: int
    status: str
    waiting_order: int | None
    registration_code: str
    registered_at: datetime
    canceled_at: datetime | None
    start_time: datetime
    end_time: datetime
    location: str
    user_account: str = ""
    user_name: str = ""


@dataclass(frozen=True)
class RegistrationResult:
    success: bool
    message: str
    registration: RegistrationDTO | None = None
    registrations: list[RegistrationDTO] | None = None
    promoted_registration: RegistrationDTO | None = None


class IRegistrationService(ABC):
    @abstractmethod
    def register_activity(self, current_user: Any, activity_id: int) -> RegistrationResult:
        raise NotImplementedError

    @abstractmethod
    def cancel_registration(self, current_user: Any, registration_id: int) -> RegistrationResult:
        raise NotImplementedError

    @abstractmethod
    def list_my_registrations(self, current_user: Any) -> RegistrationResult:
        raise NotImplementedError

    @abstractmethod
    def list_activity_registrations(self, current_user: Any, activity_id: int) -> RegistrationResult:
        raise NotImplementedError
