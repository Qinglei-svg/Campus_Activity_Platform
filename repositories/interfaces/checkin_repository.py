from __future__ import annotations

from abc import ABC, abstractmethod

from models.checkin_model import CheckinRecord


class ICheckinRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[CheckinRecord]:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, checkin_id: int) -> CheckinRecord | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_registration(self, registration_id: int) -> CheckinRecord | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_activity_and_user(self, activity_id: int, user_id: int) -> CheckinRecord | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_activity(self, activity_id: int) -> list[CheckinRecord]:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[CheckinRecord]:
        raise NotImplementedError

    @abstractmethod
    def save(self, checkin_record: CheckinRecord) -> CheckinRecord:
        raise NotImplementedError

    @abstractmethod
    def update(self, checkin_record: CheckinRecord) -> CheckinRecord:
        raise NotImplementedError
