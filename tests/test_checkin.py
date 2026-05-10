from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from controllers.activity_controller import ActivityController
from controllers.admin_controller import AdminController
from controllers.auth_controller import AuthController
from controllers.checkin_controller import CheckinController
from controllers.registration_controller import RegistrationController
from database.db import SessionLocal, initialize_database
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository
from repositories.sqlite.sqlite_checkin_repository import SQLiteCheckinRepository


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


def _register_participant(name: str = "签到测试学生"):
    account = f"checkin_{uuid4().hex[:10]}"
    controller = AuthController()
    try:
        result = controller.register(account, name, "test123456", "13800000000")
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
        "title": title or f"签到测试活动-{uuid4().hex[:8]}",
        "category_id": category.id,
        "start_time": now + timedelta(days=2),
        "end_time": now + timedelta(days=2, hours=2),
        "signup_start_time": now - timedelta(hours=1),
        "signup_end_time": now + timedelta(days=1),
        "location": "签到测试教室",
        "capacity": 20,
        "credit": 1.0,
        "volunteer_hours": 0.0,
        "description": "用于签到测试的活动。",
        "need_signup_audit": False,
    }


def _create_online_activity(session):
    publisher = _login_user("publisher", "publisher123")
    admin = _login_user("admin", "admin123")
    activity_controller = ActivityController(session=session, current_user=publisher)
    draft = activity_controller.create_draft(_activity_data(session))
    assert draft.success is True
    submitted = activity_controller.submit_activity(draft.activity.activity_id)
    assert submitted.success is True
    approved = AdminController(session=session, current_user=admin).approve_activity(submitted.activity.activity_id)
    assert approved.success is True
    return publisher, approved.activity


def _register_for_activity(session, participant, activity_id: int):
    result = RegistrationController(session=session, current_user=participant).register_activity(activity_id)
    assert result.success is True
    assert result.registration.status == "registered"
    return result.registration


def test_publisher_can_enable_password_checkin() -> None:
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        result = CheckinController(session=session, current_user=publisher).enable_checkin(
            activity.activity_id,
            "password",
            "ABC123",
        )

        assert result.success is True
        assert result.message == "签到已开启。"


def test_publisher_can_enable_qrcode_checkin() -> None:
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        result = CheckinController(session=session, current_user=publisher).enable_checkin(
            activity.activity_id,
            "qrcode",
            "QR123",
        )

        assert result.success is True
        assert result.qr_code_path is not None
        assert result.qr_code_path.exists()


def test_student_checkin_success_with_correct_code() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        _register_for_activity(session, participant, activity.activity_id)
        CheckinController(session=session, current_user=publisher).enable_checkin(activity.activity_id, "password", "OK123")

        result = CheckinController(session=session, current_user=participant).participant_checkin(activity.activity_id, "OK123")

        assert result.success is True
        assert result.checkin is not None
        assert result.checkin.status == "checked_in"


def test_wrong_checkin_code_fails() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        _register_for_activity(session, participant, activity.activity_id)
        CheckinController(session=session, current_user=publisher).enable_checkin(activity.activity_id, "password", "RIGHT")

        result = CheckinController(session=session, current_user=participant).participant_checkin(activity.activity_id, "WRONG")

        assert result.success is False
        assert result.message == "签到口令错误。"


def test_unregistered_user_cannot_checkin() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        CheckinController(session=session, current_user=publisher).enable_checkin(activity.activity_id, "password", "ONLY")

        result = CheckinController(session=session, current_user=participant).participant_checkin(activity.activity_id, "ONLY")

        assert result.success is False
        assert result.message == "只有已报名用户可以签到。"


def test_duplicate_checkin_fails() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        _register_for_activity(session, participant, activity.activity_id)
        CheckinController(session=session, current_user=publisher).enable_checkin(activity.activity_id, "password", "DUP")
        controller = CheckinController(session=session, current_user=participant)
        first = controller.participant_checkin(activity.activity_id, "DUP")
        second = controller.participant_checkin(activity.activity_id, "DUP")

        assert first.success is True
        assert second.success is False
        assert second.message == "你已完成签到，请勿重复签到。"


def test_publisher_corrects_checkin_and_writes_audit_log() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        registration = _register_for_activity(session, participant, activity.activity_id)

        result = CheckinController(session=session, current_user=publisher).correct_checkin(
            registration.registration_id,
            "checked_in",
            "现场核验后补签",
        )
        logs = SQLiteAuditLogRepository(session).list_all()
        checkin = SQLiteCheckinRepository(session).find_by_registration(registration.registration_id)

        assert result.success is True
        assert checkin is not None
        assert checkin.status == "checked_in"
        assert any(
            log.target_type == "checkin_record"
            and log.target_id == checkin.id
            and log.action == "correct_checkin"
            and log.reason == "现场核验后补签"
            for log in logs
        )


def test_correct_checkin_requires_reason() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        registration = _register_for_activity(session, participant, activity.activity_id)

        result = CheckinController(session=session, current_user=publisher).correct_checkin(
            registration.registration_id,
            "checked_in",
            " ",
        )

        assert result.success is False
        assert result.message == "修正原因不能为空。"
