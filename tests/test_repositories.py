from __future__ import annotations

from database.db import SessionLocal, initialize_database
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_role_repository import SQLiteRoleRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository


def setup_module() -> None:
    initialize_database()


def test_user_repository_can_find_admin_user() -> None:
    with SessionLocal() as session:
        repository = SQLiteUserRepository(session)

        user = repository.find_by_account("admin")

        assert user is not None
        assert user.name == "系统管理员"


def test_role_repository_can_find_admin_role() -> None:
    with SessionLocal() as session:
        repository = SQLiteRoleRepository(session)

        role = repository.find_by_code("admin")

        assert role is not None
        assert role.name == "系统管理员"


def test_activity_repository_can_list_online_activities() -> None:
    with SessionLocal() as session:
        repository = SQLiteActivityRepository(session)

        activities = repository.list_online()

        assert len(activities) >= 1
        assert all(activity.status == "online" for activity in activities)
