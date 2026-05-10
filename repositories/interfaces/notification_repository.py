from __future__ import annotations

from abc import ABC, abstractmethod

from models.notification_model import Notification


class INotificationRepository(ABC):
    @abstractmethod
    def find_by_id(self, notification_id: int) -> Notification | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[Notification]:
        raise NotImplementedError

    @abstractmethod
    def save(self, notification: Notification) -> Notification:
        raise NotImplementedError

    @abstractmethod
    def update(self, notification: Notification) -> Notification:
        raise NotImplementedError

    @abstractmethod
    def delete(self, notification_id: int) -> bool:
        raise NotImplementedError
