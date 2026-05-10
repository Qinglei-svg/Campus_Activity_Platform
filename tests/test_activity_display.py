from __future__ import annotations

from database.db import SessionLocal, initialize_database
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from services.impl.activity_service_impl import ActivityServiceImpl
from services.interfaces.auth_service import AuthenticatedUser
from utils.permission_checker import PermissionChecker


def setup_module() -> None:
    initialize_database()


def _service(session):
    return ActivityServiceImpl(
        activity_repository=SQLiteActivityRepository(session),
        category_repository=SQLiteActivityCategoryRepository(session),
    )


def _user(role_code: str, role_name: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=1,
        account=role_code,
        name=role_name,
        phone="",
        role_id=1,
        role_code=role_code,
        role_name=role_name,
        status="enabled",
    )


def test_activity_repository_can_find_default_online_activity() -> None:
    with SessionLocal() as session:
        repository = SQLiteActivityRepository(session)

        activities = repository.list_online()

        assert any(activity.title == "人工智能前沿讲座" for activity in activities)
        assert all(activity.status == "online" for activity in activities)


def test_activity_service_list_online_only_returns_online_activities() -> None:
    with SessionLocal() as session:
        result = _service(session).list_online_activities()

        assert result.success is True
        assert result.activities
        assert all(activity.status == "online" for activity in result.activities)


def test_activity_service_supports_keyword_search() -> None:
    with SessionLocal() as session:
        result = _service(session).list_online_activities({"keyword": "人工智能"})

        assert result.success is True
        assert result.activities
        assert all("人工智能" in activity.title for activity in result.activities)


def test_activity_service_supports_category_filter() -> None:
    with SessionLocal() as session:
        category_repository = SQLiteActivityCategoryRepository(session)
        categories = category_repository.list_enabled_categories()
        volunteer_category = next(category for category in categories if category.name == "志愿公益")

        result = _service(session).list_online_activities({"category_id": volunteer_category.id})

        assert result.success is True
        assert result.activities
        assert all(activity.category_id == volunteer_category.id for activity in result.activities)


def test_activity_service_get_activity_detail_returns_required_fields() -> None:
    with SessionLocal() as session:
        activity_repository = SQLiteActivityRepository(session)
        activity = next(activity for activity in activity_repository.list_online() if activity.title == "人工智能前沿讲座")

        result = _service(session).get_activity_detail(activity.id)

        assert result.success is True
        assert result.activity is not None
        detail = result.activity
        assert detail.title == "人工智能前沿讲座"
        assert detail.category_name == "学术讲座"
        assert detail.publisher_name
        assert detail.capacity > 0
        assert detail.remaining_count >= 0


def test_pending_review_activity_is_not_in_activity_hall_list() -> None:
    with SessionLocal() as session:
        result = _service(session).list_online_activities()

        assert result.success is True
        assert result.activities is not None
        assert all(activity.title != "社团招新宣讲会" for activity in result.activities)
        assert all(activity.status != "pending_review" for activity in result.activities)


def test_participant_has_activity_hall_menu() -> None:
    participant = _user("participant", "活动参与者")

    menus = PermissionChecker.get_allowed_menus(participant)

    assert "活动大厅" in menus


def test_publisher_and_admin_do_not_have_activity_hall_menu() -> None:
    publisher = _user("publisher", "活动发布者")
    admin = _user("admin", "系统管理员")

    assert "活动大厅" not in PermissionChecker.get_allowed_menus(publisher)
    assert "活动大厅" not in PermissionChecker.get_allowed_menus(admin)
