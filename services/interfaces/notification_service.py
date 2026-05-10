from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NotificationDTO:
    id: int
    receiver_id: int
    type: str
    title: str
    content: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None


@dataclass(frozen=True)
class NotificationResult:
    success: bool
    message: str
    notification: NotificationDTO | None = None
    notifications: list[NotificationDTO] | None = None


class INotificationService(ABC):
    @abstractmethod
    def send_to_user(self, user_id: int, title: str, content: str, type: str) -> NotificationResult:
        raise NotImplementedError

    @abstractmethod
    def list_user_notifications(self, user_id: int) -> NotificationResult:
        raise NotImplementedError

    @abstractmethod
    def mark_as_read(self, notification_id: int) -> NotificationResult:
        raise NotImplementedError

    @abstractmethod
    def delete_notification(self, notification_id: int) -> NotificationResult:
        raise NotImplementedError

    @abstractmethod
    def send_to_role(self, role_code: str, title: str, content: str, type: str) -> NotificationResult:
        raise NotImplementedError
