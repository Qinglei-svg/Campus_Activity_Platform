from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from openpyxl import load_workbook

from controllers.activity_controller import ActivityController
from controllers.admin_controller import AdminController
from controllers.auth_controller import AuthController
from controllers.export_controller import ExportController
from controllers.registration_controller import RegistrationController
from database.db import SessionLocal, initialize_database
from models.activity_model import Activity
from models.checkin_model import CheckinRecord
from models.role_model import Role
from models.user_model import User
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_registration_repository import SQLiteRegistrationRepository
from services.interfaces.auth_service import AuthenticatedUser
from utils.password_utils import hash_password


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


def _register_participant():
    account = f"export_student_{uuid4().hex[:8]}"
    controller = AuthController()
    try:
        result = controller.register(account, "导出测试学生", "test123456", "13800000000")
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
        "title": title or f"导出测试活动-{uuid4().hex[:8]}",
        "category_id": category.id,
        "start_time": now + timedelta(days=8),
        "end_time": now + timedelta(days=8, hours=2),
        "signup_start_time": now - timedelta(hours=1),
        "signup_end_time": now + timedelta(days=7),
        "location": "导出测试教室",
        "capacity": 10,
        "credit": 1.0,
        "volunteer_hours": 0.0,
        "description": "用于 Excel 导出测试的活动。",
        "need_signup_audit": False,
    }


def _create_online_activity(session, publisher, title: str | None = None):
    admin = _login_user("admin", "admin123")
    activity_controller = ActivityController(session=session, current_user=publisher)
    draft = activity_controller.create_draft(_activity_data(session, title=title))
    assert draft.success is True
    submitted = activity_controller.submit_activity(draft.activity.activity_id)
    assert submitted.success is True
    approved = AdminController(session=session, current_user=admin).approve_activity(submitted.activity.activity_id)
    assert approved.success is True
    return approved.activity


def _ensure_second_publisher(session) -> AuthenticatedUser:
    role = session.query(Role).filter(Role.code == "publisher").one()
    account = "export_other_publisher"
    user = session.query(User).filter(User.account == account).one_or_none()
    if user is None:
        user = User(
            role_id=role.id,
            account=account,
            name="导出测试其他发布者",
            password_hash=hash_password("publisher123"),
            auth_status="approved",
            status="enabled",
            phone="",
            violation_count=0,
        )
        session.add(user)
        session.commit()
    return AuthenticatedUser(
        id=user.id,
        account=user.account,
        name=user.name,
        phone=user.phone,
        role_id=role.id,
        role_code="publisher",
        role_name="活动发布者",
        status=user.status,
    )


def test_publisher_exports_own_activity_excel_successfully() -> None:
    publisher = _login_user("publisher", "publisher123")
    participant = _register_participant()
    with SessionLocal() as session:
        activity = _create_online_activity(session, publisher)
        registration_result = RegistrationController(session=session, current_user=participant).register_activity(
            activity.activity_id
        )
        assert registration_result.success is True

        registration = SQLiteRegistrationRepository(session).find_by_id(registration_result.registration.registration_id)
        session.add(
            CheckinRecord(
                activity_id=activity.activity_id,
                user_id=participant.id,
                registration_id=registration.id,
                checkin_method="manual",
                status="checked_in",
                location_info="测试签到点",
                operator_type="publisher",
                operator_id=publisher.id,
                correction_reason="",
            )
        )
        session.commit()

        result = ExportController(session=session, current_user=publisher).export_activity_registration_excel(
            activity.activity_id
        )

        assert result.success is True
        assert result.file_path is not None
        assert result.file_path.exists()

        workbook = load_workbook(result.file_path)
        sheet = workbook.active
        header = [cell.value for cell in sheet[1]]
        row = [cell.value for cell in sheet[2]]

        assert header == ["活动标题", "用户账号", "用户姓名", "报名状态", "报名时间", "候补顺序", "签到状态"]
        assert row[0] == activity.title
        assert row[1] == participant.account
        assert row[2] == participant.name
        assert row[3] == "已报名"
        assert row[6] == "已签到"


def test_publisher_cannot_export_other_publishers_activity() -> None:
    publisher = _login_user("publisher", "publisher123")
    with SessionLocal() as session:
        other_publisher = _ensure_second_publisher(session)
        category = next(iter(SQLiteActivityCategoryRepository(session).list_enabled_categories()))
        now = datetime.now().replace(microsecond=0)
        other_activity = Activity(
            publisher_id=other_publisher.id,
            category_id=category.id,
            title=f"别人导出活动-{uuid4().hex[:8]}",
            cover_image="",
            description="别人发布的活动。",
            start_time=now + timedelta(days=5),
            end_time=now + timedelta(days=5, hours=2),
            signup_start_time=now - timedelta(hours=1),
            signup_end_time=now + timedelta(days=4),
            location="其他地点",
            capacity=20,
            signup_condition="",
            need_signup_audit=False,
            credit=0,
            volunteer_hours=0,
            status="online",
            checkin_code="",
            checkin_method="code",
            checkin_open=False,
            reject_reason="",
        )
        session.add(other_activity)
        session.commit()

        result = ExportController(session=session, current_user=publisher).export_activity_registration_excel(
            other_activity.id
        )

        assert result.success is False
        assert result.message == "当前角色无权执行该操作"
