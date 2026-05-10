from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.activity_model import Activity
from models.registration_model import Registration
from repositories.interfaces.activity_repository import IActivityRepository


class SQLiteActivityRepository(IActivityRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, activity_id: int) -> Activity | None:
        statement = (
            select(Activity)
            .options(joinedload(Activity.category), joinedload(Activity.publisher))
            .where(Activity.id == activity_id)
        )
        return self._session.scalar(statement)

    def list_all(self) -> list[Activity]:
        statement = (
            select(Activity)
            .options(joinedload(Activity.category), joinedload(Activity.publisher))
            .order_by(Activity.created_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def list_by_status(self, status: str) -> list[Activity]:
        statement = (
            select(Activity)
            .options(joinedload(Activity.category), joinedload(Activity.publisher))
            .where(Activity.status == status)
            .order_by(Activity.start_time.asc())
        )
        return list(self._session.scalars(statement).all())

    def list_by_publisher(self, publisher_id: int) -> list[Activity]:
        statement = (
            select(Activity)
            .options(joinedload(Activity.category), joinedload(Activity.publisher))
            .where(Activity.publisher_id == publisher_id)
            .order_by(Activity.updated_at.desc(), Activity.created_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def list_by_publisher_and_status(self, publisher_id: int, status: str) -> list[Activity]:
        statement = (
            select(Activity)
            .options(joinedload(Activity.category), joinedload(Activity.publisher))
            .where(Activity.publisher_id == publisher_id, Activity.status == status)
            .order_by(Activity.updated_at.desc(), Activity.created_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def exists_title_by_publisher(
        self,
        publisher_id: int,
        title: str,
        exclude_activity_id: int | None = None,
    ) -> bool:
        statement = select(Activity.id).where(
            Activity.publisher_id == publisher_id,
            Activity.title == title,
        )
        if exclude_activity_id is not None:
            statement = statement.where(Activity.id != exclude_activity_id)
        return self._session.scalar(statement.limit(1)) is not None

    def list_online(self) -> list[Activity]:
        return self.list_by_status("online")

    def search_online(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        status: str = "online",
    ) -> list[Activity]:
        statement = (
            select(Activity)
            .options(joinedload(Activity.category), joinedload(Activity.publisher))
            .where(Activity.status == status)
            .order_by(Activity.start_time.asc())
        )
        if keyword:
            statement = statement.where(Activity.title.like(f"%{keyword.strip()}%"))
        if category_id is not None:
            statement = statement.where(Activity.category_id == category_id)
        return list(self._session.scalars(statement).all())

    def count_registered(self, activity_id: int) -> int:
        statement = select(func.count(Registration.id)).where(
            Registration.activity_id == activity_id,
            Registration.status.in_(("registered", "approved", "checked_in")),
        )
        return int(self._session.scalar(statement) or 0)

    def count_by_category(self, category_id: int) -> int:
        statement = select(func.count(Activity.id)).where(Activity.category_id == category_id)
        return int(self._session.scalar(statement) or 0)

    def save(self, activity: Activity) -> Activity:
        self._session.add(activity)
        self._session.flush()
        return activity

    def update(self, activity: Activity) -> Activity:
        merged_activity = self._session.merge(activity)
        self._session.flush()
        return merged_activity
