from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.activity_model import Activity
from models.registration_model import Registration
from models.user_model import User
from repositories.interfaces.registration_repository import IRegistrationRepository


class SQLiteRegistrationRepository(IRegistrationRepository):
    _REGISTERED_STATUSES = ("registered", "approved", "checked_in")

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[Registration]:
        statement = (
            select(Registration)
            .options(
                joinedload(Registration.activity).joinedload(Activity.category),
                joinedload(Registration.activity).joinedload(Activity.publisher),
                joinedload(Registration.user).joinedload(User.role),
            )
            .order_by(Registration.registered_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def find_by_id(self, registration_id: int) -> Registration | None:
        statement = (
            select(Registration)
            .options(
                joinedload(Registration.activity).joinedload(Activity.category),
                joinedload(Registration.activity).joinedload(Activity.publisher),
                joinedload(Registration.user).joinedload(User.role),
            )
            .where(Registration.id == registration_id)
        )
        return self._session.scalar(statement)

    def find_by_activity_and_user(self, activity_id: int, user_id: int) -> Registration | None:
        statement = (
            select(Registration)
            .options(
                joinedload(Registration.activity).joinedload(Activity.category),
                joinedload(Registration.activity).joinedload(Activity.publisher),
                joinedload(Registration.user).joinedload(User.role),
            )
            .where(
                Registration.activity_id == activity_id,
                Registration.user_id == user_id,
            )
        )
        return self._session.scalar(statement)

    def list_by_activity(self, activity_id: int) -> list[Registration]:
        statement = (
            select(Registration)
            .options(
                joinedload(Registration.activity).joinedload(Activity.category),
                joinedload(Registration.activity).joinedload(Activity.publisher),
                joinedload(Registration.user).joinedload(User.role),
            )
            .where(Registration.activity_id == activity_id)
            .order_by(Registration.registered_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def list_by_user(self, user_id: int) -> list[Registration]:
        statement = (
            select(Registration)
            .options(
                joinedload(Registration.activity).joinedload(Activity.category),
                joinedload(Registration.activity).joinedload(Activity.publisher),
                joinedload(Registration.user).joinedload(User.role),
            )
            .where(Registration.user_id == user_id)
            .order_by(Registration.registered_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def count_registered(self, activity_id: int) -> int:
        statement = select(func.count(Registration.id)).where(
            Registration.activity_id == activity_id,
            Registration.status.in_(self._REGISTERED_STATUSES),
        )
        return int(self._session.scalar(statement) or 0)

    def count_waiting(self, activity_id: int) -> int:
        statement = select(func.count(Registration.id)).where(
            Registration.activity_id == activity_id,
            Registration.status == "waiting",
        )
        return int(self._session.scalar(statement) or 0)

    def find_first_waiting(self, activity_id: int) -> Registration | None:
        statement = (
            select(Registration)
            .options(
                joinedload(Registration.activity).joinedload(Activity.category),
                joinedload(Registration.activity).joinedload(Activity.publisher),
                joinedload(Registration.user).joinedload(User.role),
            )
            .where(
                Registration.activity_id == activity_id,
                Registration.status == "waiting",
            )
            .order_by(Registration.waiting_order.asc(), Registration.registered_at.asc())
            .limit(1)
        )
        return self._session.scalar(statement)

    def save(self, registration: Registration) -> Registration:
        self._session.add(registration)
        self._session.flush()
        return registration

    def update(self, registration: Registration) -> Registration:
        merged_registration = self._session.merge(registration)
        self._session.flush()
        return merged_registration
