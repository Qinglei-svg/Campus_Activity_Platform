from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


PERMISSION_DENIED_MESSAGE = "当前角色无权执行该操作"

ROLE_CODE_ADMIN = "admin"
ROLE_CODE_PUBLISHER = "publisher"
ROLE_CODE_PARTICIPANT = "participant"

ROLE_NAME_ADMIN = "系统管理员"
ROLE_NAME_PUBLISHER = "活动发布者"
ROLE_NAME_PARTICIPANT = "活动参与者"

ADMIN_MENUS = [
    "用户管理",
    "发布者审核",
    "活动审核",
    "活动分类",
    "举报申诉处理",
    "数据统计",
    "操作日志",
    "权限配置",
    "通知中心",
    "个人信息",
]

PUBLISHER_MENUS = [
    "创建活动",
    "我的活动",
    "报名管理",
    "签到管理",
    "活动评价",
    "活动成果",
    "数据导出",
    "通知中心",
    "个人信息",
]

PARTICIPANT_MENUS = [
    "活动大厅",
    "我的报名",
    "我的签到",
    "我的评价",
    "我的证书",
    "申请发布者",
    "举报申诉",
    "通知中心",
    "个人信息",
]

ROLE_MENUS = {
    ROLE_CODE_ADMIN: ADMIN_MENUS,
    ROLE_CODE_PUBLISHER: PUBLISHER_MENUS,
    ROLE_CODE_PARTICIPANT: PARTICIPANT_MENUS,
}

ROLE_NAME_TO_CODE = {
    ROLE_NAME_ADMIN: ROLE_CODE_ADMIN,
    ROLE_NAME_PUBLISHER: ROLE_CODE_PUBLISHER,
    ROLE_NAME_PARTICIPANT: ROLE_CODE_PARTICIPANT,
}


@dataclass(frozen=True)
class PermissionResult:
    success: bool
    message: str = ""


class PermissionChecker:
    @staticmethod
    def require_role(user: Any, allowed_roles: Iterable[str]) -> PermissionResult:
        allowed_role_codes = {PermissionChecker._normalize_role(role) for role in allowed_roles}
        if PermissionChecker._get_role_code(user) in allowed_role_codes:
            return PermissionResult(True, "权限检查通过")
        return PermissionResult(False, PERMISSION_DENIED_MESSAGE)

    @staticmethod
    def is_admin(user: Any) -> bool:
        return PermissionChecker._get_role_code(user) == ROLE_CODE_ADMIN

    @staticmethod
    def is_publisher(user: Any) -> bool:
        return PermissionChecker._get_role_code(user) == ROLE_CODE_PUBLISHER

    @staticmethod
    def is_participant(user: Any) -> bool:
        return PermissionChecker._get_role_code(user) == ROLE_CODE_PARTICIPANT

    @staticmethod
    def can_manage_activity(user: Any, activity: Any) -> bool:
        if PermissionChecker.is_admin(user):
            return True
        if not PermissionChecker.is_publisher(user):
            return False
        return getattr(activity, "publisher_id", None) == getattr(user, "id", None)

    @staticmethod
    def can_access_menu(user: Any, menu_name: str) -> PermissionResult:
        role_code = PermissionChecker._get_role_code(user)
        if menu_name in ROLE_MENUS.get(role_code, []):
            return PermissionResult(True, "权限检查通过")
        return PermissionResult(False, PERMISSION_DENIED_MESSAGE)

    @staticmethod
    def get_allowed_menus(user: Any) -> list[str]:
        role_code = PermissionChecker._get_role_code(user)
        return list(ROLE_MENUS.get(role_code, []))

    @staticmethod
    def _get_role_code(user: Any) -> str | None:
        if user is None:
            return None
        role_code = getattr(user, "role_code", None)
        if role_code:
            return PermissionChecker._normalize_role(role_code)

        role_name = getattr(user, "role_name", None)
        if role_name:
            return PermissionChecker._normalize_role(role_name)

        role = getattr(user, "role", None)
        if role is not None:
            role_code = getattr(role, "code", None)
            if role_code:
                return PermissionChecker._normalize_role(role_code)
            role_name = getattr(role, "name", None)
            if role_name:
                return PermissionChecker._normalize_role(role_name)

        return None

    @staticmethod
    def _normalize_role(role: str) -> str:
        return ROLE_NAME_TO_CODE.get(role, role)
