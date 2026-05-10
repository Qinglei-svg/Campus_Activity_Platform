from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.activity_model import Activity, ActivityCategory
from models.role_model import Role, RolePermission
from models.user_model import User
from utils.datetime_utils import add_days, current_datetime
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
    users = _ensure_users(session, roles)
    categories = _ensure_categories(session)
    _ensure_demo_activities(session, users["publisher"], categories)
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


def _ensure_demo_activities(
    session: Session,
    publisher: User,
    categories: dict[str, ActivityCategory],
) -> None:
    now = current_datetime()
    demo_activities = [
        {
            "title": "人工智能前沿讲座",
            "category": "学术讲座",
            "description": "围绕生成式人工智能、校园创新实践和未来职业发展进行分享。",
            "start_time": add_days(now, 7),
            "end_time": add_days(now, 7, hours=2),
            "signup_start_time": now,
            "signup_end_time": add_days(now, 6),
            "location": "图书馆报告厅",
            "capacity": 120,
            "signup_condition": "全校学生均可报名",
            "need_signup_audit": False,
            "credit": 1.0,
            "volunteer_hours": 0.0,
            "status": "online",
            "checkin_code": "AI2026",
        },
        {
            "title": "校园志愿服务活动",
            "category": "志愿公益",
            "description": "组织学生参与校园环境维护、秩序引导和公益宣传服务。",
            "start_time": add_days(now, 10),
            "end_time": add_days(now, 10, hours=3),
            "signup_start_time": now,
            "signup_end_time": add_days(now, 9),
            "location": "校门口志愿服务站",
            "capacity": 60,
            "signup_condition": "热心公益的在校学生",
            "need_signup_audit": False,
            "credit": 0.5,
            "volunteer_hours": 3.0,
            "status": "online",
            "checkin_code": "VOL2026",
        },
        {
            "title": "社团招新宣讲会",
            "category": "社团活动",
            "description": "社团联合会面向新生介绍社团类型、报名方式和活动安排。",
            "start_time": add_days(now, 14),
            "end_time": add_days(now, 14, hours=2),
            "signup_start_time": add_days(now, 1),
            "signup_end_time": add_days(now, 13),
            "location": "大学生活动中心",
            "capacity": 200,
            "signup_condition": "对社团活动感兴趣的学生",
            "need_signup_audit": True,
            "credit": 0.5,
            "volunteer_hours": 0.0,
            "status": "pending_review",
            "checkin_code": "CLUB2026",
        },
        {
            "title": "校园科技节开幕活动",
            "category": "校级活动",
            "description": "科技节开幕式及优秀学生项目展示。",
            "start_time": add_days(now, 21),
            "end_time": add_days(now, 21, hours=3),
            "signup_start_time": add_days(now, 5),
            "signup_end_time": add_days(now, 20),
            "location": "综合体育馆",
            "capacity": 300,
            "signup_condition": "全校学生均可报名",
            "need_signup_audit": False,
            "credit": 1.0,
            "volunteer_hours": 0.0,
            "status": "draft",
            "checkin_code": "TECH2026",
        },
        {
            "title": "校园志愿服务总结会",
            "category": "志愿公益",
            "description": "已结束的志愿服务总结和经验分享活动。",
            "start_time": add_days(now, -10),
            "end_time": add_days(now, -10, hours=2),
            "signup_start_time": add_days(now, -20),
            "signup_end_time": add_days(now, -11),
            "location": "综合楼 205",
            "capacity": 80,
            "signup_condition": "志愿服务队成员",
            "need_signup_audit": False,
            "credit": 1.0,
            "volunteer_hours": 2.0,
            "status": "finished",
            "checkin_code": "DONE2026",
        },
    ]

    for data in demo_activities:
        existing = session.scalar(select(Activity).where(Activity.title == data["title"]))
        if existing is not None:
            continue

        category = categories[data["category"]]
        session.add(
            Activity(
                publisher_id=publisher.id,
                category_id=category.id,
                title=data["title"],
                cover_image="",
                description=data["description"],
                start_time=data["start_time"],
                end_time=data["end_time"],
                signup_start_time=data["signup_start_time"],
                signup_end_time=data["signup_end_time"],
                location=data["location"],
                capacity=data["capacity"],
                signup_condition=data["signup_condition"],
                need_signup_audit=data["need_signup_audit"],
                credit=data["credit"],
                volunteer_hours=data["volunteer_hours"],
                status=data["status"],
                checkin_code=data["checkin_code"],
                checkin_method="code",
                checkin_open=False,
                reject_reason="",
            )
        )
