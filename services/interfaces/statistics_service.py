from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CategoryActivityCountDTO:
    category_id: int
    category_name: str
    activity_count: int


@dataclass(frozen=True)
class HotActivityDTO:
    activity_id: int
    title: str
    category_name: str
    publisher_name: str
    registration_count: int
    checkin_count: int


@dataclass(frozen=True)
class AdminStatisticsDTO:
    total_users: int
    total_activities: int
    total_registrations: int
    total_checkins: int
    total_reviews: int
    total_certificates: int
    category_counts: list[CategoryActivityCountDTO]
    hot_activities: list[HotActivityDTO]


@dataclass(frozen=True)
class PublisherStatisticsDTO:
    activity_count: int
    total_registrations: int
    total_checkins: int
    average_checkin_rate: float
    average_score: float


@dataclass(frozen=True)
class ParticipantStatisticsDTO:
    registration_count: int
    checkin_count: int
    review_count: int
    certificate_count: int
    earned_credit: float
    volunteer_hours: float


@dataclass(frozen=True)
class ActivityCalendarEventDTO:
    activity_id: int
    title: str
    start_time: datetime
    end_time: datetime
    location: str
    status: str


@dataclass(frozen=True)
class StatisticsResult:
    success: bool
    message: str
    admin_statistics: AdminStatisticsDTO | None = None
    publisher_statistics: PublisherStatisticsDTO | None = None
    participant_statistics: ParticipantStatisticsDTO | None = None
    calendar_events: list[ActivityCalendarEventDTO] | None = None


class IStatisticsService(ABC):
    @abstractmethod
    def get_admin_statistics(self, admin_user: Any) -> StatisticsResult:
        raise NotImplementedError

    @abstractmethod
    def get_publisher_statistics(self, current_user: Any) -> StatisticsResult:
        raise NotImplementedError

    @abstractmethod
    def get_participant_statistics(self, current_user: Any) -> StatisticsResult:
        raise NotImplementedError

    @abstractmethod
    def list_publisher_calendar_events(self, current_user: Any) -> StatisticsResult:
        raise NotImplementedError

    @abstractmethod
    def list_participant_calendar_events(self, current_user: Any) -> StatisticsResult:
        raise NotImplementedError
