from __future__ import annotations

from uuid import uuid4

from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from database.db import SessionLocal, initialize_database
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository


def setup_module() -> None:
    initialize_database()


def _register_participant(name: str = "用户管理测试学生"):
    account = f"user_mgmt_{uuid4().hex[:10]}"
    password = "test123456"
    controller = AuthController()
    try:
        result = controller.register(account, name, password, "13800000000")
        assert result.success is True
        assert result.user is not None
        return account, password, result.user
    finally:
        controller.close()


def _login_admin():
    controller = AuthController()
    try:
        result = controller.login("admin", "admin123")
        assert result.success is True
        assert result.user is not None
        return result.user
    finally:
        controller.close()


def test_student_submit_publisher_application() -> None:
    _, _, student = _register_participant()
    with SessionLocal() as session:
        result = UserController(session=session, current_user=student).submit_publisher_application(
            {
                "organization_name": "测试组织",
                "responsible_person": "测试负责人",
                "contact_info": "13800000000",
                "application_note": "希望发布校园活动。",
            }
        )

        assert result.success is True
        assert result.application is not None
        assert result.application.status == "pending"


def test_admin_approve_application_changes_student_to_publisher_after_relogin() -> None:
    account, password, student = _register_participant()
    admin = _login_admin()
    with SessionLocal() as session:
        submit_result = UserController(session=session, current_user=student).submit_publisher_application(
            {
                "organization_name": "升格测试组织",
                "responsible_person": "升格负责人",
                "contact_info": "13900000000",
                "application_note": "申请成为活动发布者。",
            }
        )
        assert submit_result.success is True

        approve_result = UserController(session=session, current_user=admin).approve_publisher_application(
            submit_result.application.application_id
        )
        assert approve_result.success is True

    auth_controller = AuthController()
    try:
        login_result = auth_controller.login(account, password)
        assert login_result.success is True
        assert login_result.user.role_code == "publisher"
        assert login_result.user.role_name == "活动发布者"
    finally:
        auth_controller.close()


def test_admin_freeze_user_and_frozen_user_cannot_login() -> None:
    account, password, student = _register_participant()
    admin = _login_admin()
    with SessionLocal() as session:
        freeze_result = UserController(session=session, current_user=admin).freeze_user(student.id)
        logs = SQLiteAuditLogRepository(session).list_all()

        assert freeze_result.success is True
        assert freeze_result.user.status == "frozen"
        assert any(
            log.target_type == "user"
            and log.target_id == student.id
            and log.action == "freeze"
            and log.result == "frozen"
            for log in logs
        )

    auth_controller = AuthController()
    try:
        login_result = auth_controller.login(account, password)
        assert login_result.success is False
        assert login_result.user is None
    finally:
        auth_controller.close()
