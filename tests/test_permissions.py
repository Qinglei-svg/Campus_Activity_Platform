from __future__ import annotations

from types import SimpleNamespace

from controllers.permission_controller import PermissionController
from services.interfaces.auth_service import AuthenticatedUser
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


def _user(user_id: int, role_code: str, role_name: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=user_id,
        account=f"{role_code}_{user_id}",
        name=f"测试用户{user_id}",
        phone="",
        role_id=user_id,
        role_code=role_code,
        role_name=role_name,
        status="enabled",
    )


def test_participant_cannot_execute_admin_action() -> None:
    controller = PermissionController()
    participant = _user(3, "participant", "活动参与者")

    result = controller.ensure_admin_action(participant)

    assert result.success is False
    assert result.message == PERMISSION_DENIED_MESSAGE


def test_publisher_cannot_review_activity() -> None:
    controller = PermissionController()
    publisher = _user(2, "publisher", "活动发布者")

    result = controller.ensure_activity_review(publisher)

    assert result.success is False
    assert result.message == PERMISSION_DENIED_MESSAGE


def test_admin_can_enter_activity_review_menu() -> None:
    admin = _user(1, "admin", "系统管理员")

    result = PermissionChecker.can_access_menu(admin, "活动审核")

    assert result.success is True


def test_publisher_can_only_manage_own_activity() -> None:
    controller = PermissionController()
    publisher = _user(2, "publisher", "活动发布者")
    own_activity = SimpleNamespace(id=1, publisher_id=2)
    other_activity = SimpleNamespace(id=2, publisher_id=99)

    own_result = controller.ensure_manage_activity(publisher, own_activity)
    other_result = controller.ensure_manage_activity(publisher, other_activity)

    assert own_result.success is True
    assert other_result.success is False
    assert other_result.message == PERMISSION_DENIED_MESSAGE
