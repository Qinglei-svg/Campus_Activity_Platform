from __future__ import annotations

from uuid import uuid4

from controllers.auth_controller import AuthController
from database.db import initialize_database


def setup_module() -> None:
    initialize_database()


def test_admin_login_success() -> None:
    controller = AuthController()
    try:
        result = controller.login("admin", "admin123")

        assert result.success is True
        assert result.user is not None
        assert result.user.account == "admin"
        assert result.user.role_code == "admin"
    finally:
        controller.close()


def test_login_fails_with_wrong_password() -> None:
    controller = AuthController()
    try:
        result = controller.login("admin", "wrong-password")

        assert result.success is False
        assert result.user is None
        assert result.message == "密码错误。"
    finally:
        controller.close()


def test_register_new_user_success() -> None:
    controller = AuthController()
    account = f"student_{uuid4().hex[:8]}"
    try:
        result = controller.register(account, "测试学生", "test123456", "13800000000")

        assert result.success is True
        assert result.user is not None
        assert result.user.account == account
        assert result.user.role_code == "participant"
    finally:
        controller.close()


def test_register_fails_when_account_exists() -> None:
    controller = AuthController()
    account = f"duplicate_{uuid4().hex[:8]}"
    try:
        first_result = controller.register(account, "测试学生", "test123456", "13800000000")
        second_result = controller.register(account, "测试学生二号", "test123456", "13900000000")

        assert first_result.success is True
        assert second_result.success is False
        assert second_result.message == "账号已存在。"
    finally:
        controller.close()
