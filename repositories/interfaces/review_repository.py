from __future__ import annotations

from abc import ABC, abstractmethod

from models.review_model import Review


class IReviewRepository(ABC):
    @abstractmethod
    def find_by_id(self, review_id: int) -> Review | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_activity_and_user(self, activity_id: int, user_id: int) -> Review | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_activity(self, activity_id: int) -> list[Review]:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[Review]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Review]:
        raise NotImplementedError

    @abstractmethod
    def save(self, review: Review) -> Review:
        raise NotImplementedError

    @abstractmethod
    def update(self, review: Review) -> Review:
        raise NotImplementedError
