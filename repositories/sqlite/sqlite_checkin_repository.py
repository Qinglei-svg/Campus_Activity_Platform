from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.activity_model import Activity
from models.checkin_model import CheckinRecord
from models.registration_model import Registration
from repositories.interfaces.checkin_repository import ICheckinRepository


class SQLiteCheckinRepository(ICheckinRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[CheckinRecord]:
        statement = (
            select(CheckinRecord)
            .options(
                joinedload(CheckinRecord.activity).joinedload(Activity.category),
                joinedload(CheckinRecord.user),
                joinedload(CheckinRecord.registration).joinedload(Registration.user),
            )
            .order_by(CheckinRecord.checkin_time.desc())
        )
        return list(self._session.scalars(statement).all())

    def find_by_id(self, checkin_id: int) -> CheckinRecord | None:
        statement = (
            select(CheckinRecord)
            .options(
                joinedload(CheckinRecord.activity).joinedload(Activity.category),
                joinedload(CheckinRecord.user),
                joinedload(CheckinRecord.registration).joinedload(Registration.user),
            )
            .where(CheckinRecord.id == checkin_id)
        )
        return self._session.scalar(statement)

    def find_by_registration(self, registration_id: int) -> CheckinRecord | None:
        return self._session.scalar(
            select(CheckinRecord)
            .options(
                joinedload(CheckinRecord.activity).joinedload(Activity.category),
                joinedload(CheckinRecord.user),
                joinedload(CheckinRecord.registration).joinedload(Registration.user),
            )
            .where(CheckinRecord.registration_id == registration_id)
        )

    def find_by_activity_and_user(self, activity_id: int, user_id: int) -> CheckinRecord | None:
        statement = (
            select(CheckinRecord)
            .options(
                joinedload(CheckinRecord.activity).joinedload(Activity.category),
                joinedload(CheckinRecord.user),
                joinedload(CheckinRecord.registration).joinedload(Registration.user),
            )
            .where(CheckinRecord.activity_id == activity_id, CheckinRecord.user_id == user_id)
        )
        return self._session.scalar(statement)

    def list_by_activity(self, activity_id: int) -> list[CheckinRecord]:
        statement = (
            select(CheckinRecord)
            .options(
                joinedload(CheckinRecord.activity).joinedload(Activity.category),
                joinedload(CheckinRecord.user),
                joinedload(CheckinRecord.registration).joinedload(Registration.user),
            )
            .where(CheckinRecord.activity_id == activity_id)
            .order_by(CheckinRecord.checkin_time.desc())
        )
        return list(self._session.scalars(statement).all())

    def list_by_user(self, user_id: int) -> list[CheckinRecord]:
        statement = (
            select(CheckinRecord)
            .options(
                joinedload(CheckinRecord.activity).joinedload(Activity.category),
                joinedload(CheckinRecord.user),
                joinedload(CheckinRecord.registration).joinedload(Registration.user),
            )
            .where(CheckinRecord.user_id == user_id)
            .order_by(CheckinRecord.checkin_time.desc())
        )
        return list(self._session.scalars(statement).all())

    def save(self, checkin_record: CheckinRecord) -> CheckinRecord:
        self._session.add(checkin_record)
        self._session.flush()
        return checkin_record

    def update(self, checkin_record: CheckinRecord) -> CheckinRecord:
        merged_record = self._session.merge(checkin_record)
        self._session.flush()
        return merged_record
