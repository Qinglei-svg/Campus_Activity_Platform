from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.activity_model import ActivityCategory
from models.role_model import Role, RolePermission
from models.user_model import User
from utils.password_utils import hash_password


DEFAULT_ROLES = [
    ("admin", "系统管理员", "负责系统配置、用户管理、活动审核和平台治理。"),
    ("publisher", "活动发布者", "负责创建活动、管理报名签到、发布成果和导出数据。"),
    ("participant", "活动参与者", "负责浏览活动、报名签到、评价活动和查看证书。"),
]

DEFAULT_CATEGORIES = [
    ("学术讲座", "学术交流、专题讲座、学科竞赛宣讲。"),
    ("文体赛事", "文化艺术、体育比赛、校园赛事。"),
    ("志愿公益", "志愿服务、公益实践、社会责任活动。"),
    ("社团活动", "学生社团组织的兴趣活动。"),
    ("校级活动", "学校层面的重点活动。"),
    ("其他", "未归入固定类型的校园活动。"),
]

# 与 login_view 快速登录一致，清理数据时仅保留这些账号
QUICK_LOGIN_ACCOUNTS = frozenset({"admin", "publisher", "student"})


DEFAULT_PERMISSIONS = {
    "admin": [
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
    ],
    "publisher": [
        "创建活动",
        "我的活动",
        "报名管理",
        "签到管理",
        "活动评价",
        "活动成果",
        "数据导出",
        "通知中心",
        "个人信息",
    ],
    "participant": [
        "活动大厅",
        "我的报名",
        "我的签到",
        "我的评价",
        "我的证书",
        "申请发布者",
        "举报申诉",
        "通知中心",
        "个人信息",
    ],
}


def initialize_default_data(session: Session) -> None:
    roles = _ensure_roles(session)
    _ensure_role_permissions(session, roles)
    _ensure_users(session, roles)
    _ensure_categories(session)
    session.commit()


def _ensure_roles(session: Session) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for code, name, description in DEFAULT_ROLES:
        role = session.scalar(select(Role).where(Role.code == code))
        if role is None:
            role = Role(code=code, name=name, description=description)
            session.add(role)
            session.flush()
        else:
            role.name = name
            role.description = description
        roles[code] = role
    return roles


def _ensure_role_permissions(session: Session, roles: dict[str, Role]) -> None:
    for role_code, module_names in DEFAULT_PERMISSIONS.items():
        role = roles[role_code]
        for module_name in module_names:
            exists = session.scalar(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.module_name == module_name,
                    RolePermission.permission_code == "view",
                )
            )
            if exists is None:
                session.add(
                    RolePermission(
                        role_id=role.id,
                        module_name=module_name,
                        permission_code="view",
                        enabled=True,
                    )
                )


def _ensure_users(session: Session, roles: dict[str, Role]) -> dict[str, User]:
    default_users = [
        ("admin", "admin123", "系统管理员", "admin"),
        ("publisher", "publisher123", "校学生会", "publisher"),
        ("student", "student123", "张三", "participant"),
    ]

    users: dict[str, User] = {}
    for account, password, name, role_code in default_users:
        user = session.scalar(select(User).where(User.account == account))
        if user is None:
            user = User(
                role_id=roles[role_code].id,
                account=account,
                name=name,
                password_hash=hash_password(password),
                auth_status="approved",
                status="enabled",
                phone="",
                violation_count=0,
            )
            session.add(user)
            session.flush()
        else:
            user.role_id = roles[role_code].id
            user.name = name
        users[account] = user
    return users


def _ensure_categories(session: Session) -> dict[str, ActivityCategory]:
    categories: dict[str, ActivityCategory] = {}
    for name, description in DEFAULT_CATEGORIES:
        category = session.scalar(select(ActivityCategory).where(ActivityCategory.name == name))
        if category is None:
            category = ActivityCategory(name=name, description=description, enabled=True)
            session.add(category)
            session.flush()
        else:
            category.description = description
        categories[name] = category
    return categories
