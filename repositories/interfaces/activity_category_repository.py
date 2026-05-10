from __future__ import annotations

from abc import ABC, abstractmethod

from models.activity_model import ActivityCategory


class IActivityCategoryRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[ActivityCategory]:
        raise NotImplementedError

    @abstractmethod
    def list_enabled_categories(self) -> list[ActivityCategory]:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, category_id: int) -> ActivityCategory | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_name(self, name: str) -> ActivityCategory | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, category: ActivityCategory) -> ActivityCategory:
        raise NotImplementedError

    @abstractmethod
    def update(self, category: ActivityCategory) -> ActivityCategory:
        raise NotImplementedError
