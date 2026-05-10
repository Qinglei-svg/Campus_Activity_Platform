from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.audit_log_model import AuditLog
from models.review_model import Review
from repositories.interfaces.activity_repository import IActivityRepository
from repositories.interfaces.audit_log_repository import IAuditLogRepository
from repositories.interfaces.checkin_repository import ICheckinRepository
from repositories.interfaces.review_repository import IReviewRepository
from services.interfaces.review_service import ReviewDTO, ReviewResult, ReviewSummaryDTO, IReviewService
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


class ReviewServiceImpl(IReviewService):
    def __init__(
        self,
        session: Session,
        activity_repository: IActivityRepository,
        checkin_repository: ICheckinRepository,
        review_repository: IReviewRepository,
        audit_log_repository: IAuditLogRepository,
    ) -> None:
        self._session = session
        self._activity_repository = activity_repository
        self._checkin_repository = checkin_repository
        self._review_repository = review_repository
        self._audit_log_repository = audit_log_repository

    def submit_review(self, current_user: Any, activity_id: int, data: dict[str, Any]) -> ReviewResult:
        if not PermissionChecker.is_participant(current_user):
            return ReviewResult(False, PERMISSION_DENIED_MESSAGE)

        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return ReviewResult(False, "活动不存在。")

        checkin = self._checkin_repository.find_by_activity_and_user(activity_id, current_user.id)
        if checkin is None or checkin.status not in {"checked_in", "corrected"}:
            return ReviewResult(False, "用户必须已签到才能评价。")

        existing = self._review_repository.find_by_activity_and_user(activity_id, current_user.id)
        if existing is not None:
            return ReviewResult(False, "你已评价该活动，请勿重复评价。")

        validation_message = self._validate_review_data(data)
        if validation_message:
            return ReviewResult(False, validation_message)

        review = Review(
            activity_id=activity_id,
            user_id=current_user.id,
            content_score=float(data["content_score"]),
            organization_score=float(data["organization_score"]),
            experience_score=float(data["experience_score"]),
            overall_score=float(data["overall_score"]),
            comment=str(data.get("comment") or "").strip(),
            status="visible",
        )
        self._review_repository.save(review)
        self._session.commit()
        review = self._review_repository.find_by_id(review.id)
        return ReviewResult(True, "评价提交成功。", review=self._to_dto(review))

    def list_activity_reviews(self, current_user: Any, activity_id: int) -> ReviewResult:
        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return ReviewResult(False, "活动不存在。")
        if not (
            PermissionChecker.is_admin(current_user)
            or (PermissionChecker.is_publisher(current_user) and activity.publisher_id == current_user.id)
        ):
            return ReviewResult(False, PERMISSION_DENIED_MESSAGE)

        reviews = [
            review
            for review in self._review_repository.list_by_activity(activity_id)
            if review.status == "visible"
        ]
        return ReviewResult(
            True,
            "查询成功。",
            reviews=[self._to_dto(review) for review in reviews],
            summary=self._summary(reviews),
        )

    def list_admin_reviews(self, current_user: Any) -> ReviewResult:
        if not PermissionChecker.is_admin(current_user):
            return ReviewResult(False, PERMISSION_DENIED_MESSAGE)
        reviews = [review for review in self._review_repository.list_all() if review.status == "visible"]
        return ReviewResult(
            True,
            "查询成功。",
            reviews=[self._to_dto(review) for review in reviews],
            summary=self._summary(reviews),
        )

    def delete_review(self, current_user: Any, review_id: int, reason: str) -> ReviewResult:
        if not PermissionChecker.is_admin(current_user):
            return ReviewResult(False, PERMISSION_DENIED_MESSAGE)
        reason = reason.strip() or "管理员删除违规评价"

        review = self._review_repository.find_by_id(review_id)
        if review is None:
            return ReviewResult(False, "评价不存在。")
        if review.status == "deleted":
            return ReviewResult(False, "评价已删除。")

        review.status = "deleted"
        self._review_repository.update(review)
        self._audit_log_repository.save(
            AuditLog(
                operator_id=current_user.id,
                target_type="review",
                target_id=review.id,
                action="delete_review",
                result="deleted",
                reason=reason,
            )
        )
        self._session.commit()
        return ReviewResult(True, "评价已删除。", review=self._to_dto(review))

    def _validate_review_data(self, data: dict[str, Any]) -> str | None:
        for key, label in [
            ("content_score", "内容质量评分"),
            ("organization_score", "组织安排评分"),
            ("experience_score", "现场体验评分"),
            ("overall_score", "整体满意度评分"),
        ]:
            try:
                value = float(data.get(key))
            except (TypeError, ValueError):
                return f"{label}必须是数字。"
            if value < 1 or value > 5:
                return f"{label}必须在 1 到 5 分之间。"
        if not str(data.get("comment") or "").strip():
            return "文字评价不能为空。"
        return None

    def _summary(self, reviews: list[Review]) -> ReviewSummaryDTO:
        if not reviews:
            return ReviewSummaryDTO(0, 0, 0, 0, 0)
        count = len(reviews)
        return ReviewSummaryDTO(
            count=count,
            average_content_score=sum(review.content_score for review in reviews) / count,
            average_organization_score=sum(review.organization_score for review in reviews) / count,
            average_experience_score=sum(review.experience_score for review in reviews) / count,
            average_overall_score=sum(review.overall_score for review in reviews) / count,
        )

    def _to_dto(self, review: Review) -> ReviewDTO:
        return ReviewDTO(
            review_id=review.id,
            activity_id=review.activity_id,
            activity_title=review.activity.title if review.activity else "",
            user_id=review.user_id,
            user_account=review.user.account if review.user else "",
            user_name=review.user.name if review.user else "",
            content_score=review.content_score,
            organization_score=review.organization_score,
            experience_score=review.experience_score,
            overall_score=review.overall_score,
            comment=review.comment,
            status=review.status,
            created_at=review.created_at,
        )
