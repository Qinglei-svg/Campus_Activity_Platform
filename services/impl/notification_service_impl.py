from __future__ import annotations

from sqlalchemy.orm import Session

from models.notification_model import Notification
from repositories.interfaces.notification_repository import INotificationRepository
from repositories.interfaces.role_repository import IRoleRepository
from repositories.interfaces.user_repository import IUserRepository
from services.interfaces.notification_service import NotificationDTO, NotificationResult, INotificationService
from utils.datetime_utils import current_datetime


class NotificationServiceImpl(INotificationService):
    def __init__(
        self,
        session: Session,
        notification_repository: INotificationRepository,
        user_repository: IUserRepository,
        role_repository: IRoleRepository,
    ) -> None:
        self._session = session
        self._notification_repository = notification_repository
        self._user_repository = user_repository
        self._role_repository = role_repository

    def send_to_user(self, user_id: int, title: str, content: str, type: str) -> NotificationResult:
        if self._user_repository.find_by_id(user_id) is None:
            return NotificationResult(False, "接收用户不存在。")
        if not title.strip() or not content.strip():
            return NotificationResult(False, "通知标题和内容不能为空。")

        notification = Notification(
            receiver_id=user_id,
            type=type,
            title=title.strip(),
            content=content.strip(),
            is_read=False,
        )
        self._notification_repository.save(notification)
        self._session.commit()
        return NotificationResult(True, "通知发送成功。", notification=self._to_dto(notification))

    def list_user_notifications(self, user_id: int) -> NotificationResult:
        notifications = self._notification_repository.list_by_user(user_id)
        return NotificationResult(
            True,
            "查询成功。",
            notifications=[self._to_dto(notification) for notification in notifications],
        )

    def mark_as_read(self, notification_id: int) -> NotificationResult:
        notification = self._notification_repository.find_by_id(notification_id)
        if notification is None:
            return NotificationResult(False, "通知不存在。")

        notification.is_read = True
        notification.read_at = current_datetime()
        self._notification_repository.update(notification)
        self._session.commit()
        return NotificationResult(True, "已标记为已读。", notification=self._to_dto(notification))

    def delete_notification(self, notification_id: int) -> NotificationResult:
        deleted = self._notification_repository.delete(notification_id)
        if not deleted:
            return NotificationResult(False, "通知不存在。")

        self._session.commit()
        return NotificationResult(True, "通知已删除。")

    def send_to_role(self, role_code: str, title: str, content: str, type: str) -> NotificationResult:
        role = self._role_repository.find_by_code(role_code)
        if role is None:
            return NotificationResult(False, "目标角色不存在。")
        if not title.strip() or not content.strip():
            return NotificationResult(False, "通知标题和内容不能为空。")

        users = [user for user in self._user_repository.list_all() if user.role_id == role.id]
        notifications: list[NotificationDTO] = []
        for user in users:
            notification = Notification(
                receiver_id=user.id,
                type=type,
                title=title.strip(),
                content=content.strip(),
                is_read=False,
            )
            self._notification_repository.save(notification)
            notifications.append(self._to_dto(notification))

        self._session.commit()
        return NotificationResult(True, "通知发送成功。", notifications=notifications)

    def _to_dto(self, notification: Notification) -> NotificationDTO:
        return NotificationDTO(
            id=notification.id,
            receiver_id=notification.receiver_id,
            type=notification.type,
            title=notification.title,
            content=notification.content,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
        )
