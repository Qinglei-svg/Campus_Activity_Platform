from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from controllers.activity_controller import ActivityController
from controllers.admin_controller import AdminController
from controllers.auth_controller import AuthController
from controllers.certificate_controller import CertificateController
from controllers.checkin_controller import CheckinController
from controllers.registration_controller import RegistrationController
from database.db import SessionLocal, initialize_database
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository


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


def _register_participant(name: str = "证书测试学生"):
    account = f"cert_{uuid4().hex[:10]}"
    controller = AuthController()
    try:
        result = controller.register(account, name, "test123456", "13800000000")
        assert result.success is True
        assert result.user is not None
        return result.user
    finally:
        controller.close()


def _activity_data(session) -> dict[str, object]:
    category = next(
        category
        for category in SQLiteActivityCategoryRepository(session).list_enabled_categories()
        if category.name == "学术讲座"
    )
    now = datetime.now().replace(microsecond=0)
    return {
        "title": f"证书测试活动-{uuid4().hex[:8]}",
        "category_id": category.id,
        "start_time": now + timedelta(days=2),
        "end_time": now + timedelta(days=2, hours=2),
        "signup_start_time": now - timedelta(hours=1),
        "signup_end_time": now + timedelta(days=1),
        "location": "证书测试教室",
        "capacity": 20,
        "credit": 1.0,
        "volunteer_hours": 2.0,
        "description": "用于电子证书测试的活动。",
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


def _register_and_checkin(session, participant, publisher, activity_id: int) -> None:
    registration = RegistrationController(session=session, current_user=participant).register_activity(activity_id)
    assert registration.success is True
    enabled = CheckinController(session=session, current_user=publisher).enable_checkin(activity_id, "password", "CERT")
    assert enabled.success is True
    checkin = CheckinController(session=session, current_user=participant).participant_checkin(activity_id, "CERT")
    assert checkin.success is True


def test_checked_in_user_can_generate_certificate() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        _register_and_checkin(session, participant, publisher, activity.activity_id)

        result = CertificateController(session=session, current_user=participant).generate_certificate(activity.activity_id)

        assert result.success is True
        assert result.certificate is not None
        assert result.certificate.file_path.exists()
        assert result.certificate.certificate_no.startswith("CERT-")


def test_user_without_checkin_cannot_generate_certificate() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        _, activity = _create_online_activity(session)
        registration = RegistrationController(session=session, current_user=participant).register_activity(activity.activity_id)
        assert registration.success is True

        result = CertificateController(session=session, current_user=participant).generate_certificate(activity.activity_id)

        assert result.success is False
        assert result.message == "只有已签到用户可以生成证书。"


def test_duplicate_generate_returns_existing_certificate() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        _register_and_checkin(session, participant, publisher, activity.activity_id)
        controller = CertificateController(session=session, current_user=participant)

        first = controller.generate_certificate(activity.activity_id)
        second = controller.generate_certificate(activity.activity_id)

        assert first.success is True
        assert second.success is True
        assert second.message == "证书已生成，已返回已有证书。"
        assert first.certificate.certificate_no == second.certificate.certificate_no
        assert first.certificate.file_path == second.certificate.file_path


def test_generated_pdf_file_exists() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        _register_and_checkin(session, participant, publisher, activity.activity_id)

        result = CertificateController(session=session, current_user=participant).generate_certificate(activity.activity_id)

        assert result.success is True
        assert result.certificate.file_path.exists()
        assert result.certificate.file_path.suffix.lower() == ".pdf"
        assert result.certificate.file_path.stat().st_size > 0
