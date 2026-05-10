from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from controllers.activity_controller import ActivityController
from controllers.admin_controller import AdminController
from controllers.auth_controller import AuthController
from controllers.notification_controller import NotificationController
from database.db import SessionLocal, initialize_database
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository


def setup_module() -> None:
    initialize_database()


def _login_user(account: str, password: str):
    controller = AuthController()
    try:
        result = controller.login(account, password)
        assert result.success is True
        assert result.user is not None
        return result.user
    finally:
        controller.close()


def _activity_data(session, title: str | None = None) -> dict[str, object]:
    category = next(
        category
        for category in SQLiteActivityCategoryRepository(session).list_enabled_categories()
        if category.name == "学术讲座"
    )
    now = datetime.now().replace(microsecond=0)
    return {
        "title": title or f"审核测试活动-{uuid4().hex[:8]}",
        "category_id": category.id,
        "start_time": now + timedelta(days=8),
        "end_time": now + timedelta(days=8, hours=2),
        "signup_start_time": now,
        "signup_end_time": now + timedelta(days=7),
        "location": "审核测试教室",
        "capacity": 80,
        "credit": 1.0,
        "volunteer_hours": 0.0,
        "description": "用于管理员活动审核测试的活动详情。",
        "need_signup_audit": False,
    }


def _create_pending_activity(session, title: str | None = None):
    publisher = _login_user("publisher", "publisher123")
    controller = ActivityController(session=session, current_user=publisher)
    draft_result = controller.create_draft(_activity_data(session, title=title))
    assert draft_result.success is True
    submit_result = controller.submit_activity(draft_result.activity.activity_id)
    assert submit_result.success is True
    return publisher, submit_result.activity


def test_admin_can_list_pending_activities() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        pending = _create_pending_activity(session)[1]
        controller = AdminController(session=session, current_user=admin)

        result = controller.list_pending_activities()

        assert result.success is True
        assert any(activity.activity_id == pending.activity_id for activity in result.activities or [])


def test_publisher_cannot_list_pending_activities() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        result = AdminController(session=session, current_user=publisher).list_pending_activities()

        assert result.success is False
        assert result.message == "当前角色无权执行该操作"


def test_participant_cannot_list_pending_activities() -> None:
    participant = _login_user("student", "student123")
    with SessionLocal() as session:
        result = AdminController(session=session, current_user=participant).list_pending_activities()

        assert result.success is False
        assert result.message == "当前角色无权执行该操作"


def test_admin_can_approve_pending_activity() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        pending = _create_pending_activity(session)[1]
        result = AdminController(session=session, current_user=admin).approve_activity(pending.activity_id)

        assert result.success is True
        assert result.activity.status == "online"


def test_approve_changes_status_to_online() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        pending = _create_pending_activity(session)[1]
        AdminController(session=session, current_user=admin).approve_activity(pending.activity_id)
        activity = SQLiteActivityRepository(session).find_by_id(pending.activity_id)

        assert activity.status == "online"


def test_publisher_receives_notification_after_approve() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        publisher, pending = _create_pending_activity(session, title=f"通过通知测试-{uuid4().hex[:8]}")
        AdminController(session=session, current_user=admin).approve_activity(pending.activity_id)
        notifications = NotificationController(session=session).list_user_notifications(publisher.id).notifications or []

        assert any(notification.title == "活动审核通过" and pending.title in notification.content for notification in notifications)


def test_approved_activity_appears_in_activity_hall() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        title = f"大厅审核通过-{uuid4().hex[:8]}"
        pending = _create_pending_activity(session, title=title)[1]
        AdminController(session=session, current_user=admin).approve_activity(pending.activity_id)
        hall_result = ActivityController(session=session).list_online_activities(keyword=title)

        assert hall_result.success is True
        assert any(activity.title == title for activity in hall_result.activities or [])


def test_admin_can_reject_pending_activity() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        pending = _create_pending_activity(session)[1]
        result = AdminController(session=session, current_user=admin).reject_activity(pending.activity_id, "资料不完整")

        assert result.success is True
        assert result.activity.status == "rejected"


def test_reject_changes_status_to_rejected() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        pending = _create_pending_activity(session)[1]
        AdminController(session=session, current_user=admin).reject_activity(pending.activity_id, "时间安排不合理")
        activity = SQLiteActivityRepository(session).find_by_id(pending.activity_id)

        assert activity.status == "rejected"


def test_reject_reason_is_saved() -> None:
    admin = _login_user("admin", "admin123")
    reason = "活动详情不够完整"
    with SessionLocal() as session:
        pending = _create_pending_activity(session)[1]
        AdminController(session=session, current_user=admin).reject_activity(pending.activity_id, reason)
        activity = SQLiteActivityRepository(session).find_by_id(pending.activity_id)

        assert activity.reject_reason == reason


def test_publisher_receives_notification_after_reject() -> None:
    admin = _login_user("admin", "admin123")
    reason = "材料缺失"
    with SessionLocal() as session:
        publisher, pending = _create_pending_activity(session, title=f"驳回通知测试-{uuid4().hex[:8]}")
        AdminController(session=session, current_user=admin).reject_activity(pending.activity_id, reason)
        notifications = NotificationController(session=session).list_user_notifications(publisher.id).notifications or []

        assert any(
            notification.title == "活动审核未通过"
            and pending.title in notification.content
            and reason in notification.content
            for notification in notifications
        )


def test_reject_fails_when_reason_is_empty() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        pending = _create_pending_activity(session)[1]
        result = AdminController(session=session, current_user=admin).reject_activity(pending.activity_id, " ")

        assert result.success is False
        assert result.message == "驳回原因不能为空。"


def test_non_pending_activity_cannot_be_reviewed_twice() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        pending = _create_pending_activity(session)[1]
        controller = AdminController(session=session, current_user=admin)
        first_result = controller.approve_activity(pending.activity_id)
        second_result = controller.approve_activity(pending.activity_id)

        assert first_result.success is True
        assert second_result.success is False
        assert second_result.message == "当前活动状态不允许审核。"


def test_audit_operation_writes_audit_log() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        pending = _create_pending_activity(session)[1]
        AdminController(session=session, current_user=admin).approve_activity(pending.activity_id)
        logs = SQLiteAuditLogRepository(session).list_all()

        assert any(
            log.target_type == "activity"
            and log.target_id == pending.activity_id
            and log.action == "approve"
            and log.result == "approved"
            for log in logs
        )
