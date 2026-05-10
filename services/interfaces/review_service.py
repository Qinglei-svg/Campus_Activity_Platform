from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ReviewDTO:
    review_id: int
    activity_id: int
    activity_title: str
    user_id: int
    user_account: str
    user_name: str
    content_score: float
    organization_score: float
    experience_score: float
    overall_score: float
    comment: str
    status: str
    created_at: datetime


@dataclass(frozen=True)
class ReviewSummaryDTO:
    count: int
    average_content_score: float
    average_organization_score: float
    average_experience_score: float
    average_overall_score: float


@dataclass(frozen=True)
class ReviewResult:
    success: bool
    message: str
    review: ReviewDTO | None = None
    reviews: list[ReviewDTO] | None = None
    summary: ReviewSummaryDTO | None = None


class IReviewService(ABC):
    @abstractmethod
    def submit_review(self, current_user: Any, activity_id: int, data: dict[str, Any]) -> ReviewResult:
        raise NotImplementedError

    @abstractmethod
    def list_activity_reviews(self, current_user: Any, activity_id: int) -> ReviewResult:
        raise NotImplementedError

    @abstractmethod
    def list_admin_reviews(self, current_user: Any) -> ReviewResult:
        raise NotImplementedError

    @abstractmethod
    def delete_review(self, current_user: Any, review_id: int, reason: str) -> ReviewResult:
        raise NotImplementedError
