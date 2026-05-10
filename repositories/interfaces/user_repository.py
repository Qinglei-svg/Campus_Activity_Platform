from __future__ import annotations

from abc import ABC, abstractmethod

from models.user_model import PublisherApplication, User


class IUserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id: int) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_account(self, account: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    def list_by_role_code(self, role_code: str) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    def save(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    def update(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    def save_publisher_application(self, application: PublisherApplication) -> PublisherApplication:
        raise NotImplementedError

    @abstractmethod
    def update_publisher_application(self, application: PublisherApplication) -> PublisherApplication:
        raise NotImplementedError

    @abstractmethod
    def find_publisher_application_by_id(self, application_id: int) -> PublisherApplication | None:
        raise NotImplementedError

    @abstractmethod
    def find_pending_publisher_application_by_user(self, user_id: int) -> PublisherApplication | None:
        raise NotImplementedError

    @abstractmethod
    def list_publisher_applications(self, status: str | None = None) -> list[PublisherApplication]:
        raise NotImplementedError
