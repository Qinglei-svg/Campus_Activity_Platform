from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from controllers.activity_controller import ActivityController
from controllers.admin_controller import AdminController
from controllers.auth_controller import AuthController
from controllers.checkin_controller import CheckinController
from controllers.registration_controller import RegistrationController
from controllers.review_controller import ReviewController
from database.db import SessionLocal, initialize_database
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_audit_log_repository import SQLiteAuditLogRepository


def setup_module() -> None:
    initialize_database()


def _login_user(account: str, password: str):
    controller = AuthController()
    try:
        result = controller.login(account, password)
        assert result.success is True
        assert result.user is not None
        return result.user
    finally:
        controller.close()


def _register_participant(name: str = "评价测试学生"):
    account = f"review_{uuid4().hex[:10]}"
    controller = AuthController()
    try:
        result = controller.register(account, name, "test123456", "13800000000")
        assert result.success is True
        assert result.user is not None
        return result.user
    finally:
        controller.close()


def _activity_data(session) -> dict[str, object]:
    category = next(
        category
        for category in SQLiteActivityCategoryRepository(session).list_enabled_categories()
        if category.name == "学术讲座"
    )
    now = datetime.now().replace(microsecond=0)
    return {
        "title": f"评价测试活动-{uuid4().hex[:8]}",
        "category_id": category.id,
        "start_time": now + timedelta(days=2),
        "end_time": now + timedelta(days=2, hours=2),
        "signup_start_time": now - timedelta(hours=1),
        "signup_end_time": now + timedelta(days=1),
        "location": "评价测试教室",
        "capacity": 20,
        "credit": 1.0,
        "volunteer_hours": 0.0,
        "description": "用于评价功能测试的活动。",
        "need_signup_audit": False,
    }


def _create_online_activity(session):
    publisher = _login_user("publisher", "publisher123")
    admin = _login_user("admin", "admin123")
    activity_controller = ActivityController(session=session, current_user=publisher)
    draft = activity_controller.create_draft(_activity_data(session))
    assert draft.success is True
    submitted = activity_controller.submit_activity(draft.activity.activity_id)
    assert submitted.success is True
    approved = AdminController(session=session, current_user=admin).approve_activity(submitted.activity.activity_id)
    assert approved.success is True
    return publisher, approved.activity


def _review_data(comment: str = "活动内容充实，组织安排清晰。") -> dict[str, object]:
    return {
        "content_score": 5,
        "organization_score": 4,
        "experience_score": 5,
        "overall_score": 5,
        "comment": comment,
    }


def _register_and_checkin(session, participant, publisher, activity_id: int) -> None:
    registration = RegistrationController(session=session, current_user=participant).register_activity(activity_id)
    assert registration.success is True
    enabled = CheckinController(session=session, current_user=publisher).enable_checkin(activity_id, "password", "REVIEW")
    assert enabled.success is True
    checkin = CheckinController(session=session, current_user=participant).participant_checkin(activity_id, "REVIEW")
    assert checkin.success is True


def test_checked_in_user_can_submit_review() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        _register_and_checkin(session, participant, publisher, activity.activity_id)

        result = ReviewController(session=session, current_user=participant).submit_review(
            activity.activity_id,
            _review_data(),
        )

        assert result.success is True
        assert result.review is not None
        assert result.review.overall_score == 5


def test_user_without_checkin_cannot_submit_review() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        registration = RegistrationController(session=session, current_user=participant).register_activity(activity.activity_id)
        assert registration.success is True

        result = ReviewController(session=session, current_user=participant).submit_review(
            activity.activity_id,
            _review_data(),
        )

        assert result.success is False
        assert result.message == "用户必须已签到才能评价。"


def test_duplicate_review_fails() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        _register_and_checkin(session, participant, publisher, activity.activity_id)
        controller = ReviewController(session=session, current_user=participant)
        first = controller.submit_review(activity.activity_id, _review_data("第一次评价。"))
        second = controller.submit_review(activity.activity_id, _review_data("第二次评价。"))

        assert first.success is True
        assert second.success is False
        assert second.message == "你已评价该活动，请勿重复评价。"


def test_publisher_can_view_own_activity_reviews() -> None:
    participant = _register_participant()
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        _register_and_checkin(session, participant, publisher, activity.activity_id)
        ReviewController(session=session, current_user=participant).submit_review(activity.activity_id, _review_data())

        result = ReviewController(session=session, current_user=publisher).list_activity_reviews(activity.activity_id)

        assert result.success is True
        assert result.reviews
        assert result.summary is not None
        assert result.summary.count >= 1


def test_admin_can_delete_review_and_write_audit_log() -> None:
    participant = _register_participant()
    admin = _login_user("admin", "admin123")
    with SessionLocal() as session:
        publisher, activity = _create_online_activity(session)
        _register_and_checkin(session, participant, publisher, activity.activity_id)
        review = ReviewController(session=session, current_user=participant).submit_review(
            activity.activity_id,
            _review_data("包含违规内容的评价。"),
        )
        assert review.success is True

        result = ReviewController(session=session, current_user=admin).delete_review(
            review.review.review_id,
            "违规内容",
        )
        logs = SQLiteAuditLogRepository(session).list_all()

        assert result.success is True
        assert result.review.status == "deleted"
        assert any(
            log.target_type == "review"
            and log.target_id == review.review.review_id
            and log.action == "delete_review"
            and log.reason == "违规内容"
            for log in logs
        )
