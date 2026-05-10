from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.activity_model import Activity
from models.certificate_model import Certificate
from models.user_model import User
from repositories.interfaces.certificate_repository import ICertificateRepository


class SQLiteCertificateRepository(ICertificateRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[Certificate]:
        statement = (
            select(Certificate)
            .options(
                joinedload(Certificate.activity).joinedload(Activity.category),
                joinedload(Certificate.user).joinedload(User.role),
            )
            .order_by(Certificate.generated_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def find_by_id(self, certificate_id: int) -> Certificate | None:
        statement = (
            select(Certificate)
            .options(
                joinedload(Certificate.activity).joinedload(Activity.category),
                joinedload(Certificate.user).joinedload(User.role),
            )
            .where(Certificate.id == certificate_id)
        )
        return self._session.scalar(statement)

    def find_by_user_and_activity(self, user_id: int, activity_id: int) -> Certificate | None:
        statement = (
            select(Certificate)
            .options(
                joinedload(Certificate.activity).joinedload(Activity.category),
                joinedload(Certificate.user).joinedload(User.role),
            )
            .where(Certificate.user_id == user_id, Certificate.activity_id == activity_id)
        )
        return self._session.scalar(statement)

    def list_by_user(self, user_id: int) -> list[Certificate]:
        statement = (
            select(Certificate)
            .options(
                joinedload(Certificate.activity).joinedload(Activity.category),
                joinedload(Certificate.user).joinedload(User.role),
            )
            .where(Certificate.user_id == user_id)
            .order_by(Certificate.generated_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def list_by_activity(self, activity_id: int) -> list[Certificate]:
        statement = (
            select(Certificate)
            .options(
                joinedload(Certificate.activity).joinedload(Activity.category),
                joinedload(Certificate.user).joinedload(User.role),
            )
            .where(Certificate.activity_id == activity_id)
            .order_by(Certificate.generated_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def save(self, certificate: Certificate) -> Certificate:
        self._session.add(certificate)
        self._session.flush()
        return certificate
