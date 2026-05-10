from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from controllers.activity_controller import ActivityController
from controllers.auth_controller import AuthController
from controllers.category_controller import CategoryController
from database.db import SessionLocal, initialize_database
from database.init_data import DEFAULT_CATEGORIES
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository


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


def _category_controller(session, user) -> CategoryController:
    return CategoryController(session=session, current_user=user)


def _activity_controller(session, user) -> ActivityController:
    return ActivityController(session=session, current_user=user)


def _activity_data(category_id: int, title: str | None = None) -> dict[str, object]:
    now = datetime.now().replace(microsecond=0)
    return {
        "title": title or f"分类历史活动-{uuid4().hex[:8]}",
        "category_id": category_id,
        "start_time": now + timedelta(days=8),
        "end_time": now + timedelta(days=8, hours=2),
        "signup_start_time": now,
        "signup_end_time": now + timedelta(days=7),
        "location": "分类测试教室",
        "capacity": 30,
        "credit": 1.0,
        "volunteer_hours": 0.0,
        "description": "用于验证活动分类管理的测试活动。",
        "need_signup_audit": False,
    }


def _unique_category_name(prefix: str = "测试分类") -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def test_admin_can_create_activity_category() -> None:
    admin = _login("admin", "admin123")
    with SessionLocal() as session:
        result = _category_controller(session, admin).create_category(
            _unique_category_name(),
            "管理员新增分类测试",
        )

        assert result.success is True
        assert result.category is not None
        assert result.category.enabled is True


def test_publisher_and_participant_cannot_manage_categories() -> None:
    admin = _login("admin", "admin123")
    publisher = _login("publisher", "publisher123")
    participant = _login("student", "student123")
    with SessionLocal() as session:
        created = _category_controller(session, admin).create_category(_unique_category_name(), "权限测试")
        assert created.success is True

        publisher_update = _category_controller(session, publisher).update_category(
            created.category.category_id,
            "发布者越权分类",
            "不应成功",
        )
        participant_disable = _category_controller(session, participant).disable_category(
            created.category.category_id
        )

        assert publisher_update.success is False
        assert participant_disable.success is False
        assert publisher_update.message == "当前角色无权执行该操作"
        assert participant_disable.message == "当前角色无权执行该操作"


def test_category_name_cannot_be_empty_or_duplicate() -> None:
    admin = _login("admin", "admin123")
    with SessionLocal() as session:
        controller = _category_controller(session, admin)
        name = _unique_category_name()
        created = controller.create_category(name, "查重测试")
        empty = controller.create_category("   ", "空名称测试")
        duplicate = controller.create_category(f" {name} ", "重复名称测试")

        assert created.success is True
        assert empty.success is False
        assert duplicate.success is False
        assert empty.message == "分类名称不能为空。"
        assert duplicate.message == "分类名称不能重复。"


def test_admin_can_update_and_disable_category() -> None:
    admin = _login("admin", "admin123")
    with SessionLocal() as session:
        controller = _category_controller(session, admin)
        created = controller.create_category(_unique_category_name(), "待编辑")
        new_name = _unique_category_name("已编辑分类")

        updated = controller.update_category(created.category.category_id, new_name, "已编辑描述")
        disabled = controller.disable_category(created.category.category_id)

        assert updated.success is True
        assert updated.category.name == new_name
        assert updated.category.description == "已编辑描述"
        assert disabled.success is True
        assert disabled.category.enabled is False


def test_disabled_category_is_hidden_from_publisher_category_list() -> None:
    admin = _login("admin", "admin123")
    with SessionLocal() as session:
        controller = _category_controller(session, admin)
        created = controller.create_category(_unique_category_name(), "下拉框禁用测试")
        controller.disable_category(created.category.category_id)

        activity_result = ActivityController(session=session, current_user=admin).list_categories()

        assert activity_result.success is True
        assert all(
            category.category_id != created.category.category_id
            for category in activity_result.categories or []
        )


def test_publisher_cannot_create_activity_with_disabled_category() -> None:
    admin = _login("admin", "admin123")
    publisher = _login("publisher", "publisher123")
    with SessionLocal() as session:
        created = _category_controller(session, admin).create_category(_unique_category_name(), "禁用创建测试")
        _category_controller(session, admin).disable_category(created.category.category_id)

        result = _activity_controller(session, publisher).create_draft(
            _activity_data(created.category.category_id)
        )

        assert result.success is False
        assert result.message == "活动分类不存在或已禁用。"


def test_disabled_category_keeps_historical_activity_category_name() -> None:
    admin = _login("admin", "admin123")
    publisher = _login("publisher", "publisher123")
    with SessionLocal() as session:
        category = _category_controller(session, admin).create_category(
            _unique_category_name("历史分类"),
            "历史活动显示测试",
        ).category
        activity_controller = _activity_controller(session, publisher)
        created_activity = activity_controller.create_draft(
            _activity_data(category.category_id, title=f"历史分类活动-{uuid4().hex[:8]}")
        )
        assert created_activity.success is True

        _category_controller(session, admin).disable_category(category.category_id)
        detail = activity_controller.get_my_activity_detail(created_activity.activity.activity_id)

        assert detail.success is True
        assert detail.activity.category_name == category.name


def test_admin_category_list_contains_activity_count() -> None:
    admin = _login("admin", "admin123")
    publisher = _login("publisher", "publisher123")
    with SessionLocal() as session:
        category = _category_controller(session, admin).create_category(
            _unique_category_name("统计分类"),
            "分类统计测试",
        ).category
        created_activity = _activity_controller(session, publisher).create_draft(
            _activity_data(category.category_id)
        )
        assert created_activity.success is True

        result = _category_controller(session, admin).list_categories()
        matched = next(item for item in result.categories or [] if item.category_id == category.category_id)

        assert matched.activity_count == 1


def test_default_categories_are_not_inserted_repeatedly() -> None:
    initialize_database()
    initialize_database()
    default_names = [name for name, _ in DEFAULT_CATEGORIES]
    with SessionLocal() as session:
        categories = SQLiteActivityCategoryRepository(session).list_all()
        counts = {
            name: sum(1 for category in categories if category.name == name)
            for name in default_names
        }

        assert all(count == 1 for count in counts.values())
