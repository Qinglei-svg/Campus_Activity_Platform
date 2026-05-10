from __future__ import annotations

from abc import ABC, abstractmethod

from models.certificate_model import Certificate


class ICertificateRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Certificate]:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, certificate_id: int) -> Certificate | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_user_and_activity(self, user_id: int, activity_id: int) -> Certificate | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[Certificate]:
        raise NotImplementedError

    @abstractmethod
    def list_by_activity(self, activity_id: int) -> list[Certificate]:
        raise NotImplementedError

    @abstractmethod
    def save(self, certificate: Certificate) -> Certificate:
        raise NotImplementedError
