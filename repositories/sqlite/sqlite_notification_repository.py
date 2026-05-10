from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.notification_model import Notification
from repositories.interfaces.notification_repository import INotificationRepository


class SQLiteNotificationRepository(INotificationRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, notification_id: int) -> Notification | None:
        return self._session.get(Notification, notification_id)

    def list_by_user(self, user_id: int) -> list[Notification]:
        statement = (
            select(Notification)
            .where(Notification.receiver_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def save(self, notification: Notification) -> Notification:
        self._session.add(notification)
        self._session.flush()
        return notification

    def update(self, notification: Notification) -> Notification:
        merged_notification = self._session.merge(notification)
        self._session.flush()
        return merged_notification

    def delete(self, notification_id: int) -> bool:
        notification = self._session.get(Notification, notification_id)
        if notification is None:
            return False
        self._session.delete(notification)
        self._session.flush()
        return True
