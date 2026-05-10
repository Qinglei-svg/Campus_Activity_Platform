from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from controllers.activity_controller import ActivityController
from controllers.admin_controller import AdminController
from controllers.auth_controller import AuthController
from controllers.registration_controller import RegistrationController
from database.db import SessionLocal, initialize_database
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_registration_repository import SQLiteRegistrationRepository


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


def _register_participant(name_prefix: str = "报名测试学生"):
    account = f"reg_{uuid4().hex[:10]}"
    controller = AuthController()
    try:
        result = controller.register(account, name_prefix, "test123456", "13800000000")
        assert result.success is True
        assert result.user is not None
        return result.user
    finally:
        controller.close()


def _activity_data(session, capacity: int = 5, title: str | None = None) -> dict[str, object]:
    category = next(
        category
        for category in SQLiteActivityCategoryRepository(session).list_enabled_categories()
        if category.name == "学术讲座"
    )
    now = datetime.now().replace(microsecond=0)
    return {
        "title": title or f"报名测试活动-{uuid4().hex[:8]}",
        "category_id": category.id,
        "start_time": now + timedelta(days=8),
        "end_time": now + timedelta(days=8, hours=2),
        "signup_start_time": now - timedelta(hours=1),
        "signup_end_time": now + timedelta(days=7),
        "location": "报名测试教室",
        "capacity": capacity,
        "credit": 1.0,
        "volunteer_hours": 0.0,
        "description": "用于报名测试的已上线活动。",
        "need_signup_audit": False,
    }


def _create_online_activity(session, capacity: int = 5):
    publisher = _login_user("publisher", "publisher123")
    admin = _login_user("admin", "admin123")
    activity_controller = ActivityController(session=session, current_user=publisher)
    draft = activity_controller.create_draft(_activity_data(session, capacity=capacity))
    assert draft.success is True
    submitted = activity_controller.submit_activity(draft.activity.activity_id)
    assert submitted.success is True
    approved = AdminController(session=session, current_user=admin).approve_activity(submitted.activity.activity_id)
    assert approved.success is True
    return approved.activity


def _create_draft_activity(session):
    publisher = _login_user("publisher", "publisher123")
    activity_controller = ActivityController(session=session, current_user=publisher)
    draft = activity_controller.create_draft(_activity_data(session, capacity=5))
    assert draft.success is True
    return draft.activity


def test_participant_can_register_online_activity() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        activity = _create_online_activity(session)
        result = RegistrationController(session=session, current_user=participant).register_activity(activity.activity_id)

        assert result.success is True
        assert result.registration is not None
        assert result.registration.status == "registered"


def test_participant_cannot_register_same_activity_twice() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        activity = _create_online_activity(session)
        controller = RegistrationController(session=session, current_user=participant)
        first = controller.register_activity(activity.activity_id)
        second = controller.register_activity(activity.activity_id)

        assert first.success is True
        assert second.success is False
        assert second.message == "你已报名该活动，请勿重复报名。"


def test_full_activity_puts_later_participant_into_waiting_list() -> None:
    first_user = _register_participant("第一位学生")
    second_user = _register_participant("第二位学生")
    with SessionLocal() as session:
        activity = _create_online_activity(session, capacity=1)
        first = RegistrationController(session=session, current_user=first_user).register_activity(activity.activity_id)
        second = RegistrationController(session=session, current_user=second_user).register_activity(activity.activity_id)

        assert first.registration.status == "registered"
        assert second.success is True
        assert second.registration.status == "waiting"
        assert second.registration.waiting_order == 1


def test_cancel_registered_promotes_first_waiting_user() -> None:
    first_user = _register_participant("已报名学生")
    second_user = _register_participant("候补学生")
    with SessionLocal() as session:
        activity = _create_online_activity(session, capacity=1)
        first = RegistrationController(session=session, current_user=first_user).register_activity(activity.activity_id)
        waiting = RegistrationController(session=session, current_user=second_user).register_activity(activity.activity_id)
        assert waiting.registration.status == "waiting"

        cancel_result = RegistrationController(session=session, current_user=first_user).cancel_registration(
            first.registration.registration_id
        )
        promoted = SQLiteRegistrationRepository(session).find_by_id(waiting.registration.registration_id)

        assert cancel_result.success is True
        assert promoted.status == "registered"
        assert promoted.waiting_order is None


def test_cancel_waiting_registration_does_not_promote_anyone() -> None:
    first_user = _register_participant("已报名学生")
    second_user = _register_participant("候补学生")
    with SessionLocal() as session:
        activity = _create_online_activity(session, capacity=1)
        RegistrationController(session=session, current_user=first_user).register_activity(activity.activity_id)
        waiting = RegistrationController(session=session, current_user=second_user).register_activity(activity.activity_id)

        cancel_result = RegistrationController(session=session, current_user=second_user).cancel_registration(
            waiting.registration.registration_id
        )

        assert cancel_result.success is True
        assert cancel_result.promoted_registration is None
        assert SQLiteRegistrationRepository(session).count_registered(activity.activity_id) == 1


def test_publisher_cannot_register_activity() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        activity = _create_online_activity(session)
        result = RegistrationController(session=session, current_user=publisher).register_activity(activity.activity_id)

        assert result.success is False
        assert result.message == "当前角色无权执行该操作"


def test_participant_cannot_register_non_online_activity() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        draft = _create_draft_activity(session)
        result = RegistrationController(session=session, current_user=participant).register_activity(draft.activity_id)

        assert result.success is False
        assert result.message == "当前活动不可报名。"


def test_participant_can_list_my_registrations() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        activity = _create_online_activity(session)
        registration = RegistrationController(session=session, current_user=participant).register_activity(activity.activity_id)

        result = RegistrationController(session=session, current_user=participant).list_my_registrations()

        assert result.success is True
        assert any(item.registration_id == registration.registration.registration_id for item in result.registrations or [])


def test_cancel_registration_marks_record_canceled() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        activity = _create_online_activity(session)
        registration = RegistrationController(session=session, current_user=participant).register_activity(activity.activity_id)

        result = RegistrationController(session=session, current_user=participant).cancel_registration(
            registration.registration.registration_id
        )
        stored = SQLiteRegistrationRepository(session).find_by_id(registration.registration.registration_id)

        assert result.success is True
        assert stored.status == "canceled"
        assert stored.canceled_at is not None


def test_activity_remaining_count_changes_after_registration() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        activity = _create_online_activity(session, capacity=2)
        before = ActivityController(session=session).get_activity_detail(activity.activity_id).activity
        RegistrationController(session=session, current_user=participant).register_activity(activity.activity_id)
        after = ActivityController(session=session).get_activity_detail(activity.activity_id).activity

        assert before.remaining_count == 2
        assert after.remaining_count == 1
        assert SQLiteActivityRepository(session).count_registered(activity.activity_id) == 1
