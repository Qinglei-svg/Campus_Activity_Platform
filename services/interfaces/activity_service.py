from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ActivityCategoryDTO:
    category_id: int
    name: str
    description: str


@dataclass(frozen=True)
class ActivityDTO:
    activity_id: int
    title: str
    category_id: int
    category_name: str
    publisher_id: int
    publisher_name: str
    start_time: datetime
    end_time: datetime
    signup_start_time: datetime
    signup_end_time: datetime
    location: str
    capacity: int
    registered_count: int
    remaining_count: int
    credit: float
    volunteer_hours: float
    status: str
    description: str
    need_signup_audit: bool
    reject_reason: str
    updated_at: datetime


@dataclass(frozen=True)
class ActivityResult:
    success: bool
    message: str
    activity: ActivityDTO | None = None
    activities: list[ActivityDTO] | None = None
    categories: list[ActivityCategoryDTO] | None = None


class IActivityService(ABC):
    @abstractmethod
    def list_online_activities(self, filters: dict[str, Any] | None = None) -> ActivityResult:
        raise NotImplementedError

    @abstractmethod
    def get_activity_detail(self, activity_id: int, current_user: Any | None = None) -> ActivityResult:
        raise NotImplementedError

    @abstractmethod
    def list_categories(self) -> ActivityResult:
        raise NotImplementedError

    @abstractmethod
    def create_draft(self, current_user: Any, data: dict[str, Any]) -> ActivityResult:
        raise NotImplementedError

    @abstractmethod
    def update_activity(self, current_user: Any, activity_id: int, data: dict[str, Any]) -> ActivityResult:
        raise NotImplementedError

    @abstractmethod
    def submit_activity(self, current_user: Any, activity_id: int) -> ActivityResult:
        raise NotImplementedError

    @abstractmethod
    def list_my_activities(self, current_user: Any, status: str | None = None) -> ActivityResult:
        raise NotImplementedError

    @abstractmethod
    def get_my_activity_detail(self, current_user: Any, activity_id: int) -> ActivityResult:
        raise NotImplementedError
