from __future__ import annotations

from uuid import uuid4

from controllers.auth_controller import AuthController
from controllers.notification_controller import NotificationController
from database.db import initialize_database


def setup_module() -> None:
    initialize_database()


def test_student_can_receive_read_and_delete_notification() -> None:
    auth_controller = AuthController()
    notification_controller = NotificationController()
    title = f"测试通知-{uuid4().hex[:8]}"

    try:
        login_result = auth_controller.login("student", "student123")
        assert login_result.success is True
        assert login_result.user is not None
        student_id = login_result.user.id

        send_result = notification_controller.send_to_user(
            student_id,
            title,
            "这是一条本地通知测试内容。",
            "system",
        )
        assert send_result.success is True
        assert send_result.notification is not None

        list_result = notification_controller.list_user_notifications(student_id)
        assert list_result.success is True
        notifications = list_result.notifications or []
        created_notification = next(notification for notification in notifications if notification.title == title)
        assert created_notification.is_read is False

        read_result = notification_controller.mark_as_read(created_notification.id)
        assert read_result.success is True
        assert read_result.notification is not None
        assert read_result.notification.is_read is True

        delete_result = notification_controller.delete_notification(created_notification.id)
        assert delete_result.success is True

        after_delete_result = notification_controller.list_user_notifications(student_id)
        assert after_delete_result.success is True
        after_delete_notifications = after_delete_result.notifications or []
        assert all(notification.id != created_notification.id for notification in after_delete_notifications)
    finally:
        auth_controller.close()
        notification_controller.close()
