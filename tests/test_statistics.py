from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from controllers.auth_controller import AuthController
from controllers.statistics_controller import StatisticsController
from database.db import SessionLocal, initialize_database
from models.activity_model import Activity
from models.certificate_model import Certificate
from models.checkin_model import CheckinRecord
from models.registration_model import Registration
from models.review_model import Review
from models.role_model import Role
from models.user_model import User
from repositories.sqlite.sqlite_activity_category_repository import SQLiteActivityCategoryRepository
from repositories.sqlite.sqlite_activity_repository import SQLiteActivityRepository
from repositories.sqlite.sqlite_certificate_repository import SQLiteCertificateRepository
from repositories.sqlite.sqlite_checkin_repository import SQLiteCheckinRepository
from repositories.sqlite.sqlite_registration_repository import SQLiteRegistrationRepository
from repositories.sqlite.sqlite_review_repository import SQLiteReviewRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from utils.password_utils import hash_password


def setup_module() -> None:
    initialize_database()


def _login(account: str, password: str):
    controller = AuthController()
    try:
        result = controller.login(account, password)
        assert result.success is True
        assert result.user is not None
        return result.user
    finally:
        controller.close()


def _create_user(session, role_code: str, prefix: str) -> tuple[str, str, User]:
    role = session.query(Role).filter(Role.code == role_code).one()
    account = f"{prefix}_{uuid4().hex[:8]}"
    password = "test123456"
    user = User(
        role_id=role.id,
        account=account,
        name=f"{prefix}用户",
        password_hash=hash_password(password),
        auth_status="approved",
        status="enabled",
        phone="",
        violation_count=0,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return account, password, user


def _create_activity(session, publisher_id: int, title_prefix: str = "统计测试活动", credit: float = 1.0, hours: float = 2.0) -> Activity:
    category = next(iter(SQLiteActivityCategoryRepository(session).list_enabled_categories()))
    now = datetime.now().replace(microsecond=0)
    activity = Activity(
        publisher_id=publisher_id,
        category_id=category.id,
        title=f"{title_prefix}-{uuid4().hex[:8]}",
        cover_image="",
        description="用于数据统计测试的活动。",
        start_time=now + timedelta(days=3),
        end_time=now + timedelta(days=3, hours=2),
        signup_start_time=now - timedelta(days=1),
        signup_end_time=now + timedelta(days=2),
        location="统计测试教室",
        capacity=50,
        signup_condition="",
        need_signup_audit=False,
        credit=credit,
        volunteer_hours=hours,
        status="online",
        checkin_code="STAT",
        checkin_method="code",
        checkin_open=True,
        reject_reason="",
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def _create_registration_bundle(
    session,
    activity: Activity,
    participant: User,
    checked_in: bool = True,
    reviewed: bool = True,
    certificated: bool = True,
) -> Registration:
    registration = Registration(
        activity_id=activity.id,
        user_id=participant.id,
        status="registered",
        waiting_order=None,
        registration_code=f"REG-{uuid4().hex[:12].upper()}",
        registered_at=datetime.now().replace(microsecond=0),
        canceled_at=None,
    )
    session.add(registration)
    session.flush()
    if checked_in:
        session.add(
            CheckinRecord(
                activity_id=activity.id,
                user_id=participant.id,
                registration_id=registration.id,
                checkin_method="password",
                status="checked_in",
                location_info="",
                operator_type="user",
                operator_id=participant.id,
                correction_reason="",
            )
        )
    if reviewed:
        session.add(
            Review(
                activity_id=activity.id,
                user_id=participant.id,
                content_score=4,
                organization_score=5,
                experience_score=4,
                overall_score=4,
                comment="统计测试评价",
                status="visible",
            )
        )
    if certificated:
        session.add(
            Certificate(
                user_id=participant.id,
                activity_id=activity.id,
                certificate_no=f"CERT-{uuid4().hex[:12].upper()}",
                certificate_type="participation",
                file_path="data/certificates/stat-test.pdf",
            )
        )
    session.commit()
    session.refresh(registration)
    return registration


def test_admin_statistics_numbers_are_correct() -> None:
    admin = _login("admin", "admin123")
    with SessionLocal() as session:
        _, _, publisher = _create_user(session, "publisher", "admin_stat_pub")
        _, _, participant = _create_user(session, "participant", "admin_stat_stu")
        activity = _create_activity(session, publisher.id)
        _create_registration_bundle(session, activity, participant)

        result = StatisticsController(session=session, current_user=admin).get_admin_statistics()

        assert result.success is True
        statistics = result.admin_statistics
        assert statistics.total_users == len(SQLiteUserRepository(session).list_all())
        assert statistics.total_activities == len(SQLiteActivityRepository(session).list_all())
        assert statistics.total_registrations == len(SQLiteRegistrationRepository(session).list_all())
        assert statistics.total_checkins == len(SQLiteCheckinRepository(session).list_all())
        assert statistics.total_reviews == len(SQLiteReviewRepository(session).list_all())
        assert statistics.total_certificates == len(SQLiteCertificateRepository(session).list_all())
        assert any(item.activity_count >= 1 for item in statistics.category_counts)
        assert statistics.hot_activities
        registration_counts = [item.registration_count for item in statistics.hot_activities]
        assert registration_counts == sorted(registration_counts, reverse=True)


def test_publisher_statistics_only_counts_own_activities() -> None:
    with SessionLocal() as session:
        pub_account, pub_password, publisher = _create_user(session, "publisher", "pub_stat_owner")
        _, _, other_publisher = _create_user(session, "publisher", "pub_stat_other")
        _, _, participant = _create_user(session, "participant", "pub_stat_stu")
        own_activity = _create_activity(session, publisher.id, title_prefix="发布者自己活动")
        other_activity = _create_activity(session, other_publisher.id, title_prefix="其他发布者活动")
        _create_registration_bundle(session, own_activity, participant)
        _, _, other_participant = _create_user(session, "participant", "pub_stat_other_stu")
        _create_registration_bundle(session, other_activity, other_participant)

    publisher_user = _login(pub_account, pub_password)
    with SessionLocal() as session:
        result = StatisticsController(session=session, current_user=publisher_user).get_publisher_statistics()

        assert result.success is True
        statistics = result.publisher_statistics
        assert statistics.activity_count == 1
        assert statistics.total_registrations == 1
        assert statistics.total_checkins == 1
        assert statistics.average_checkin_rate == 1
        assert statistics.average_score == 4


def test_participant_statistics_only_counts_own_records() -> None:
    with SessionLocal() as session:
        _, _, publisher = _create_user(session, "publisher", "part_stat_pub")
        participant_account, participant_password, participant = _create_user(session, "participant", "part_stat_owner")
        _, _, other_participant = _create_user(session, "participant", "part_stat_other")
        own_activity = _create_activity(session, publisher.id, credit=1.5, hours=3.0)
        other_activity = _create_activity(session, publisher.id, credit=2.0, hours=4.0)
        _create_registration_bundle(session, own_activity, participant)
        _create_registration_bundle(session, other_activity, other_participant)

    participant_user = _login(participant_account, participant_password)
    with SessionLocal() as session:
        result = StatisticsController(session=session, current_user=participant_user).get_participant_statistics()
        calendar_result = StatisticsController(session=session, current_user=participant_user).list_participant_calendar_events()

        assert result.success is True
        statistics = result.participant_statistics
        assert statistics.registration_count == 1
        assert statistics.checkin_count == 1
        assert statistics.review_count == 1
        assert statistics.certificate_count == 1
        assert statistics.earned_credit == 1.5
        assert statistics.volunteer_hours == 3.0
        assert calendar_result.success is True
        assert len(calendar_result.calendar_events or []) == 1
