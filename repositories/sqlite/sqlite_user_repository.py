from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.user_model import User
from models.role_model import Role
from models.user_model import PublisherApplication
from repositories.interfaces.user_repository import IUserRepository


class SQLiteUserRepository(IUserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, user_id: int) -> User | None:
        return self._session.scalar(
            select(User).options(joinedload(User.role)).where(User.id == user_id)
        )

    def find_by_account(self, account: str) -> User | None:
        return self._session.scalar(
            select(User).options(joinedload(User.role)).where(User.account == account)
        )

    def list_all(self) -> list[User]:
        return list(self._session.scalars(select(User).options(joinedload(User.role)).order_by(User.id)).all())

    def list_by_role_code(self, role_code: str) -> list[User]:
        statement = (
            select(User)
            .join(User.role)
            .options(joinedload(User.role))
            .where(Role.code == role_code)
            .order_by(User.id)
        )
        return list(self._session.scalars(statement).all())

    def save(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user

    def update(self, user: User) -> User:
        merged_user = self._session.merge(user)
        self._session.flush()
        return merged_user

    def save_publisher_application(self, application: PublisherApplication) -> PublisherApplication:
        self._session.add(application)
        self._session.flush()
        return application

    def update_publisher_application(self, application: PublisherApplication) -> PublisherApplication:
        merged_application = self._session.merge(application)
        self._session.flush()
        return merged_application

    def find_publisher_application_by_id(self, application_id: int) -> PublisherApplication | None:
        statement = (
            select(PublisherApplication)
            .options(joinedload(PublisherApplication.user).joinedload(User.role))
            .where(PublisherApplication.id == application_id)
        )
        return self._session.scalar(statement)

    def find_pending_publisher_application_by_user(self, user_id: int) -> PublisherApplication | None:
        statement = (
            select(PublisherApplication)
            .options(joinedload(PublisherApplication.user).joinedload(User.role))
            .where(PublisherApplication.user_id == user_id, PublisherApplication.status == "pending")
            .order_by(PublisherApplication.submitted_at.desc())
            .limit(1)
        )
        return self._session.scalar(statement)

    def list_publisher_applications(self, status: str | None = None) -> list[PublisherApplication]:
        statement = (
            select(PublisherApplication)
            .options(joinedload(PublisherApplication.user).joinedload(User.role))
            .order_by(PublisherApplication.submitted_at.desc())
        )
        if status:
            statement = statement.where(PublisherApplication.status == status)
        return list(self._session.scalars(statement).all())
