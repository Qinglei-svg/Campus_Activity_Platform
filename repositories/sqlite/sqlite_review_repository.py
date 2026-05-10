from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.activity_model import Activity
from models.review_model import Review
from models.user_model import User
from repositories.interfaces.review_repository import IReviewRepository


class SQLiteReviewRepository(IReviewRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, review_id: int) -> Review | None:
        statement = (
            select(Review)
            .options(
                joinedload(Review.activity).joinedload(Activity.category),
                joinedload(Review.activity).joinedload(Activity.publisher),
                joinedload(Review.user).joinedload(User.role),
            )
            .where(Review.id == review_id)
        )
        return self._session.scalar(statement)

    def find_by_activity_and_user(self, activity_id: int, user_id: int) -> Review | None:
        statement = (
            select(Review)
            .options(
                joinedload(Review.activity).joinedload(Activity.category),
                joinedload(Review.activity).joinedload(Activity.publisher),
                joinedload(Review.user).joinedload(User.role),
            )
            .where(
                Review.activity_id == activity_id,
                Review.user_id == user_id,
            )
        )
        return self._session.scalar(statement)

    def list_by_activity(self, activity_id: int) -> list[Review]:
        statement = (
            select(Review)
            .options(
                joinedload(Review.activity).joinedload(Activity.category),
                joinedload(Review.activity).joinedload(Activity.publisher),
                joinedload(Review.user).joinedload(User.role),
            )
            .where(Review.activity_id == activity_id)
            .order_by(Review.created_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def list_by_user(self, user_id: int) -> list[Review]:
        statement = (
            select(Review)
            .options(
                joinedload(Review.activity).joinedload(Activity.category),
                joinedload(Review.activity).joinedload(Activity.publisher),
                joinedload(Review.user).joinedload(User.role),
            )
            .where(Review.user_id == user_id)
            .order_by(Review.created_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def list_all(self) -> list[Review]:
        statement = (
            select(Review)
            .options(
                joinedload(Review.activity).joinedload(Activity.category),
                joinedload(Review.activity).joinedload(Activity.publisher),
                joinedload(Review.user).joinedload(User.role),
            )
            .order_by(Review.created_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def save(self, review: Review) -> Review:
        self._session.add(review)
        self._session.flush()
        return review

    def update(self, review: Review) -> Review:
        merged_review = self._session.merge(review)
        self._session.flush()
        return merged_review
