from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from controllers.activity_controller import ActivityController
from controllers.auth_controller import AuthController
from controllers.notification_controller import NotificationController
from database.db import SessionLocal, initialize_database
from models.activity_model import Activity
from models.role_model import Role
from models.user_model import User
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from utils.password_utils import hash_password


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


def _base_data(session, title: str | None = None) -> dict[str, object]:
    category = next(
        category
        for category in SQLiteActivityCategoryRepository(session).list_enabled_categories()
        if category.name == "学术讲座"
    )
    now = datetime.now().replace(microsecond=0)
    return {
        "title": title or f"发布测试活动-{uuid4().hex[:8]}",
        "category_id": category.id,
        "start_time": now + timedelta(days=7),
        "end_time": now + timedelta(days=7, hours=2),
        "signup_start_time": now,
        "signup_end_time": now + timedelta(days=6),
        "location": "测试教室 101",
        "capacity": 50,
        "credit": 1.0,
        "volunteer_hours": 0.0,
        "description": "这是发布者活动管理测试使用的活动详情。",
        "need_signup_audit": False,
    }


def _activity_controller(session, user) -> ActivityController:
    return ActivityController(session=session, current_user=user)


def _ensure_second_publisher(session) -> User:
    role = session.query(Role).filter(Role.code == "publisher").one()
    account = "publisher_two"
    user = session.query(User).filter(User.account == account).one_or_none()
    if user is None:
        user = User(
            role_id=role.id,
            account=account,
            name="第二发布者",
            password_hash=hash_password("publisher123"),
            auth_status="approved",
            status="enabled",
            phone="",
            violation_count=0,
        )
        session.add(user)
        session.commit()
    return user


def test_publisher_can_create_draft_activity() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        controller = _activity_controller(session, publisher)

        result = controller.create_draft(_base_data(session))

        assert result.success is True
        assert result.activity is not None
        assert result.activity.status == "draft"


def test_participant_cannot_create_activity() -> None:
    participant = _login_user("student", "student123")
    with SessionLocal() as session:
        controller = _activity_controller(session, participant)

        result = controller.create_draft(_base_data(session))

        assert result.success is False
        assert result.message == "当前角色无权执行该操作"


def test_admin_cannot_create_publisher_draft_activity() -> None:
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        controller = _activity_controller(session, admin)

        result = controller.create_draft(_base_data(session))

        assert result.success is False
        assert result.message == "当前角色无权执行该操作"


def test_create_activity_fails_when_title_is_empty() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        data = _base_data(session)
        data["title"] = " "

        result = _activity_controller(session, publisher).create_draft(data)

        assert result.success is False
        assert result.message == "活动标题不能为空。"


def test_create_activity_fails_when_capacity_is_not_positive() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        data = _base_data(session)
        data["capacity"] = 0

        result = _activity_controller(session, publisher).create_draft(data)

        assert result.success is False
        assert result.message == "活动容量必须是正整数。"


def test_create_activity_fails_when_end_time_is_before_start_time() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        data = _base_data(session)
        data["end_time"] = data["start_time"] - timedelta(hours=1)

        result = _activity_controller(session, publisher).create_draft(data)

        assert result.success is False
        assert result.message == "活动开始时间不能晚于结束时间。"


def test_publisher_can_list_own_activities() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        controller = _activity_controller(session, publisher)
        created = controller.create_draft(_base_data(session))
        assert created.success is True

        result = controller.list_my_activities()

        assert result.success is True
        assert any(activity.activity_id == created.activity.activity_id for activity in result.activities or [])


def test_publisher_cannot_view_or_edit_other_publishers_activity() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        other_user = _ensure_second_publisher(session)
        other_activity = Activity(
            publisher_id=other_user.id,
            category_id=_base_data(session)["category_id"],
            title=f"他人活动-{uuid4().hex[:8]}",
            cover_image="",
            description="他人创建的活动。",
            start_time=_base_data(session)["start_time"],
            end_time=_base_data(session)["end_time"],
            signup_start_time=_base_data(session)["signup_start_time"],
            signup_end_time=_base_data(session)["signup_end_time"],
            location="他人活动地点",
            capacity=30,
            signup_condition="",
            need_signup_audit=False,
            credit=0,
            volunteer_hours=0,
            status="draft",
            checkin_code="",
            checkin_method="code",
            checkin_open=False,
            reject_reason="",
        )
        session.add(other_activity)
        session.commit()

        controller = _activity_controller(session, publisher)
        detail_result = controller.get_my_activity_detail(other_activity.id)
        update_result = controller.update_activity(other_activity.id, _base_data(session))

        assert detail_result.success is False
        assert update_result.success is False
        assert detail_result.message == "当前角色无权执行该操作"
        assert update_result.message == "当前角色无权执行该操作"


def test_draft_activity_can_be_submitted_for_review() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        controller = _activity_controller(session, publisher)
        created = controller.create_draft(_base_data(session))
        assert created.success is True

        result = controller.submit_activity(created.activity.activity_id)

        assert result.success is True
        assert result.activity.status == "pending_review"


def test_submit_changes_status_to_pending_review() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        controller = _activity_controller(session, publisher)
        created = controller.create_draft(_base_data(session))
        controller.submit_activity(created.activity.activity_id)

        activity = SQLiteActivityRepository(session).find_by_id(created.activity.activity_id)

        assert activity.status == "pending_review"


def test_rejected_activity_can_be_resubmitted() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        controller = _activity_controller(session, publisher)
        created = controller.create_draft(_base_data(session))
        activity = SQLiteActivityRepository(session).find_by_id(created.activity.activity_id)
        activity.status = "rejected"
        activity.reject_reason = "材料不完整"
        session.commit()

        result = controller.submit_activity(activity.id)

        assert result.success is True
        assert result.activity.status == "pending_review"
        assert result.activity.reject_reason == ""


def test_pending_review_activity_cannot_be_edited() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        controller = _activity_controller(session, publisher)
        created = controller.create_draft(_base_data(session))
        controller.submit_activity(created.activity.activity_id)

        data = _base_data(session)
        data["title"] = f"编辑失败-{uuid4().hex[:8]}"
        result = controller.update_activity(created.activity.activity_id, data)

        assert result.success is False
        assert result.message == "当前活动状态不允许编辑。"


def test_admin_receives_notification_after_submit() -> None:
    publisher = _login_user("publisher", "publisher123")
    admin = _login_user("admin", "admin123")
    title = f"通知联动测试-{uuid4().hex[:8]}"
    with SessionLocal() as session:
        controller = _activity_controller(session, publisher)
        created = controller.create_draft(_base_data(session, title=title))
        result = controller.submit_activity(created.activity.activity_id)
        assert result.success is True

    notification_controller = NotificationController()
    try:
        notifications = notification_controller.list_user_notifications(admin.id).notifications or []
        matched = [notification for notification in notifications if title in notification.content]
        assert matched
        assert matched[0].title == "有新的活动待审核"
        assert "校学生会" in matched[0].content
    finally:
        notification_controller.close()


def test_activity_hall_still_only_shows_online_activities() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        controller = _activity_controller(session, publisher)
        draft = controller.create_draft(_base_data(session, title=f"大厅草稿过滤-{uuid4().hex[:8]}"))
        pending = controller.create_draft(_base_data(session, title=f"大厅待审过滤-{uuid4().hex[:8]}"))
        controller.submit_activity(pending.activity.activity_id)

        hall_result = controller.list_online_activities()
        titles = {activity.title for activity in hall_result.activities or []}

        assert draft.activity.title not in titles
        assert pending.activity.title not in titles
        assert all(activity.status == "online" for activity in hall_result.activities or [])
