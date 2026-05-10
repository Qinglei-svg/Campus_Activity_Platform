from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.activity_model import ActivityCategory
from repositories.interfaces.activity_category_repository import IActivityCategoryRepository


class SQLiteActivityCategoryRepository(IActivityCategoryRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[ActivityCategory]:
        statement = select(ActivityCategory).order_by(ActivityCategory.id.asc())
        return list(self._session.scalars(statement).all())

    def list_enabled_categories(self) -> list[ActivityCategory]:
        statement = (
            select(ActivityCategory)
            .where(ActivityCategory.enabled.is_(True))
            .order_by(ActivityCategory.id.asc())
        )
        return list(self._session.scalars(statement).all())

    def find_by_id(self, category_id: int) -> ActivityCategory | None:
        return self._session.get(ActivityCategory, category_id)

    def find_by_name(self, name: str) -> ActivityCategory | None:
        return self._session.scalar(select(ActivityCategory).where(ActivityCategory.name == name))

    def save(self, category: ActivityCategory) -> ActivityCategory:
        self._session.add(category)
        self._session.flush()
        return category

    def update(self, category: ActivityCategory) -> ActivityCategory:
        merged_category = self._session.merge(category)
        self._session.flush()
        return merged_category
