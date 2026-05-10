from __future__ import annotations

from abc import ABC, abstractmethod

from models.registration_model import Registration


class IRegistrationRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Registration]:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, registration_id: int) -> Registration | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_activity_and_user(self, activity_id: int, user_id: int) -> Registration | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_activity(self, activity_id: int) -> list[Registration]:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[Registration]:
        raise NotImplementedError

    @abstractmethod
    def count_registered(self, activity_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_waiting(self, activity_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def find_first_waiting(self, activity_id: int) -> Registration | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, registration: Registration) -> Registration:
        raise NotImplementedError

    @abstractmethod
    def update(self, registration: Registration) -> Registration:
        raise NotImplementedError
