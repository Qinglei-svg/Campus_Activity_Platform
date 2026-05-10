from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from controllers.auth_controller import AuthController
from controllers.report_appeal_controller import ReportAppealController
from database.db import SessionLocal, initialize_database
from models.activity_model import Activity
from models.role_model import Role
from models.user_model import User
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository
from repositories.sqlite.sqlite_report_appeal_repository import SQLiteReportAppealRepository
from utils.password_utils import hash_password


def setup_module() -> None:
    initialize_database()


def _login(account: str, password: str):
    controller = AuthController()
    try:
        result = controller.login(account, password)
        assert result.success is True
        assert result.user is not None
        return result.user
    finally:
        controller.close()


def _register_participant(prefix: str = "report_student"):
    account = f"{prefix}_{uuid4().hex[:8]}"
    password = "test123456"
    controller = AuthController()
    try:
        result = controller.register(account, f"举报测试学生{uuid4().hex[:4]}", password, "13800000000")
        assert result.success is True
        assert result.user is not None
        return account, password, result.user
    finally:
        controller.close()


def _create_publisher(session, prefix: str = "report_publisher") -> tuple[str, str, User]:
    role = session.query(Role).filter(Role.code == "publisher").one()
    account = f"{prefix}_{uuid4().hex[:8]}"
    password = "publisher123"
    user = User(
        role_id=role.id,
        account=account,
        name=f"举报测试发布者{uuid4().hex[:4]}",
        password_hash=hash_password(password),
        auth_status="approved",
        status="enabled",
        phone="",
        violation_count=0,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return account, password, user


def _create_online_activity(session, publisher_id: int) -> Activity:
    category = next(iter(SQLiteActivityCategoryRepository(session).list_enabled_categories()))
    now = datetime.now().replace(microsecond=0)
    activity = Activity(
        publisher_id=publisher_id,
        category_id=category.id,
        title=f"举报测试活动-{uuid4().hex[:8]}",
        cover_image="",
        description="用于举报申诉测试的已上线活动。",
        start_time=now + timedelta(days=5),
        end_time=now + timedelta(days=5, hours=2),
        signup_start_time=now,
        signup_end_time=now + timedelta(days=4),
        location="举报测试教室",
        capacity=20,
        signup_condition="",
        need_signup_audit=False,
        credit=1.0,
        volunteer_hours=0.0,
        status="online",
        checkin_code="REPORT",
        checkin_method="code",
        checkin_open=False,
        reject_reason="",
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def test_participant_can_report_activity_and_publisher() -> None:
    _, _, participant = _register_participant()
    with SessionLocal() as session:
        _, _, publisher = _create_publisher(session)
        activity = _create_online_activity(session, publisher.id)
        controller = ReportAppealController(session=session, current_user=participant)

        activity_report = controller.submit_activity_report(activity.id, "活动信息存在误导。")
        publisher_report = controller.submit_publisher_report(publisher.id, "发布者沟通态度恶劣。")

        assert activity_report.success is True
        assert activity_report.report.status == "pending"
        assert activity_report.report.target_type == "activity"
        assert publisher_report.success is True
        assert publisher_report.report.target_type == "publisher"


def test_publisher_can_report_participant() -> None:
    _, _, participant = _register_participant()
    with SessionLocal() as session:
        publisher_account, publisher_password, participant_target = _create_publisher(session)
        publisher_user = _login(publisher_account, publisher_password)
        controller = ReportAppealController(session=session, current_user=publisher_user)

        result = controller.submit_participant_report(participant.id, "参与者恶意占用名额。")

        assert result.success is True
        assert result.report.target_type == "participant"
        assert result.report.target_user_id == participant.id


def test_invalid_roles_cannot_submit_wrong_report_types() -> None:
    _, _, participant = _register_participant()
    publisher_user = _login("publisher", "publisher123")
    with SessionLocal() as session:
        _, _, publisher = _create_publisher(session)
        activity = _create_online_activity(session, publisher.id)

        publisher_report_activity = ReportAppealController(
            session=session,
            current_user=publisher_user,
        ).submit_activity_report(activity.id, "发布者不能举报活动。")
        participant_report_participant = ReportAppealController(
            session=session,
            current_user=participant,
        ).submit_participant_report(participant.id, "参与者不能举报参与者。")

        assert publisher_report_activity.success is False
        assert participant_report_participant.success is False


def test_admin_can_list_pending_reports() -> None:
    admin = _login("admin", "admin123")
    _, _, participant = _register_participant()
    with SessionLocal() as session:
        _, _, publisher = _create_publisher(session)
        created = ReportAppealController(session=session, current_user=participant).submit_publisher_report(
            publisher.id,
            "待处理列表测试。",
        )
        assert created.success is True

        result = ReportAppealController(session=session, current_user=admin).list_reports(status="pending")

        assert result.success is True
        assert any(report.report_id == created.report.report_id for report in result.reports or [])


def test_non_admin_cannot_handle_report() -> None:
    _, _, participant = _register_participant()
    with SessionLocal() as session:
        _, _, publisher = _create_publisher(session)
        created = ReportAppealController(session=session, current_user=participant).submit_publisher_report(
            publisher.id,
            "越权处理测试。",
        )

        result = ReportAppealController(session=session, current_user=participant).punish_report(
            created.report.report_id
        )

        assert result.success is False
        assert result.message == "当前角色无权执行该操作"


def test_admin_punish_report_freezes_target_for_one_day_and_writes_log() -> None:
    admin = _login("admin", "admin123")
    reporter_account, _, reporter = _register_participant()
    with SessionLocal() as session:
        target_account, target_password, target = _create_publisher(session)
        created = ReportAppealController(session=session, current_user=reporter).submit_publisher_report(
            target.id,
            "处罚测试。",
        )

        result = ReportAppealController(session=session, current_user=admin).punish_report(created.report.report_id)
        stored_target = session.query(User).filter(User.id == target.id).one()
        logs = SQLiteAuditLogRepository(session).list_all()

        assert result.success is True
        assert result.report.status == "punished"
        assert stored_target.status == "frozen"
        assert stored_target.frozen_until is not None
        assert stored_target.frozen_until > datetime.now()
        assert stored_target.violation_count == 1
        assert any(
            log.target_type == "report_appeal"
            and log.target_id == created.report.report_id
            and log.action == "punish"
            for log in logs
        )

    controller = AuthController()
    try:
        login_result = controller.login(target_account, target_password)
        assert login_result.success is False
    finally:
        controller.close()


def test_admin_ignore_report_does_not_freeze_target() -> None:
    admin = _login("admin", "admin123")
    _, _, participant = _register_participant()
    with SessionLocal() as session:
        target_account, target_password, target = _create_publisher(session)
        created = ReportAppealController(session=session, current_user=participant).submit_publisher_report(
            target.id,
            "不处理测试。",
        )

        result = ReportAppealController(session=session, current_user=admin).ignore_report(
            created.report.report_id,
            "证据不足，不做处理。",
        )
        stored_target = session.query(User).filter(User.id == target.id).one()

        assert result.success is True
        assert result.report.status == "ignored"
        assert stored_target.status == "enabled"

    login_result = AuthController().login(target_account, target_password)
    assert login_result.success is True


def test_expired_temporary_freeze_allows_login_again() -> None:
    account, password, user = _register_participant("expired_freeze")
    with SessionLocal() as session:
        stored_user = session.query(User).filter(User.id == user.id).one()
        stored_user.status = "frozen"
        stored_user.frozen_until = datetime.now() - timedelta(minutes=1)
        session.commit()

    controller = AuthController()
    try:
        result = controller.login(account, password)
        assert result.success is True
        with SessionLocal() as session:
            stored_user = session.query(User).filter(User.id == user.id).one()
            assert stored_user.status == "enabled"
            assert stored_user.frozen_until is None
    finally:
        controller.close()
