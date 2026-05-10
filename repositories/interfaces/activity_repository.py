from __future__ import annotations

from abc import ABC, abstractmethod

from models.activity_model import Activity


class IActivityRepository(ABC):
    @abstractmethod
    def find_by_id(self, activity_id: int) -> Activity | None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Activity]:
        raise NotImplementedError

    @abstractmethod
    def list_by_status(self, status: str) -> list[Activity]:
        raise NotImplementedError

    @abstractmethod
    def list_by_publisher(self, publisher_id: int) -> list[Activity]:
        raise NotImplementedError

    @abstractmethod
    def list_by_publisher_and_status(self, publisher_id: int, status: str) -> list[Activity]:
        raise NotImplementedError

    @abstractmethod
    def exists_title_by_publisher(
        self,
        publisher_id: int,
        title: str,
        exclude_activity_id: int | None = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_online(self) -> list[Activity]:
        raise NotImplementedError

    @abstractmethod
    def search_online(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        status: str = "online",
    ) -> list[Activity]:
        raise NotImplementedError

    @abstractmethod
    def count_registered(self, activity_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_by_category(self, category_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def save(self, activity: Activity) -> Activity:
        raise NotImplementedError

    @abstractmethod
    def update(self, activity: Activity) -> Activity:
        raise NotImplementedError
