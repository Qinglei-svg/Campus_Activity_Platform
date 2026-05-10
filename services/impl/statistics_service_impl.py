from __future__ import annotations

from typing import Any

from models.activity_model import Activity
from models.registration_model import Registration
from repositories.interfaces.activity_category_repository import IActivityCategoryRepository
from repositories.interfaces.activity_repository import IActivityRepository
from repositories.interfaces.certificate_repository import ICertificateRepository
from repositories.interfaces.checkin_repository import ICheckinRepository
from repositories.interfaces.registration_repository import IRegistrationRepository
from repositories.interfaces.review_repository import IReviewRepository
from repositories.interfaces.user_repository import IUserRepository
from services.interfaces.statistics_service import (
    ActivityCalendarEventDTO,
    AdminStatisticsDTO,
    CategoryActivityCountDTO,
    HotActivityDTO,
    ParticipantStatisticsDTO,
    PublisherStatisticsDTO,
    StatisticsResult,
    IStatisticsService,
)
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


ACTIVE_REGISTRATION_STATUSES = {"registered", "approved", "checked_in", "waiting"}
VALID_CHECKIN_STATUSES = {"checked_in", "corrected"}


class StatisticsServiceImpl(IStatisticsService):
    def __init__(
        self,
        user_repository: IUserRepository,
        activity_repository: IActivityRepository,
        category_repository: IActivityCategoryRepository,
        registration_repository: IRegistrationRepository,
        checkin_repository: ICheckinRepository,
        review_repository: IReviewRepository,
        certificate_repository: ICertificateRepository,
    ) -> None:
        self._user_repository = user_repository
        self._activity_repository = activity_repository
        self._category_repository = category_repository
        self._registration_repository = registration_repository
        self._checkin_repository = checkin_repository
        self._review_repository = review_repository
        self._certificate_repository = certificate_repository

    def get_admin_statistics(self, admin_user: Any) -> StatisticsResult:
        if not PermissionChecker.is_admin(admin_user):
            return StatisticsResult(False, PERMISSION_DENIED_MESSAGE)

        users = self._user_repository.list_all()
        activities = self._activity_repository.list_all()
        registrations = self._registration_repository.list_all()
        checkins = self._checkin_repository.list_all()
        reviews = self._review_repository.list_all()
        certificates = self._certificate_repository.list_all()
        category_counts = [
            CategoryActivityCountDTO(
                category_id=category.id,
                category_name=category.name,
                activity_count=self._activity_repository.count_by_category(category.id),
            )
            for category in self._category_repository.list_all()
        ]
        hot_activities = sorted(
            [self._to_hot_activity(activity) for activity in activities],
            key=lambda item: item.registration_count,
            reverse=True,
        )[:10]

        return StatisticsResult(
            True,
            "查询成功。",
            admin_statistics=AdminStatisticsDTO(
                total_users=len(users),
                total_activities=len(activities),
                total_registrations=len(registrations),
                total_checkins=len(checkins),
                total_reviews=len(reviews),
                total_certificates=len(certificates),
                category_counts=category_counts,
                hot_activities=hot_activities,
            ),
        )

    def get_publisher_statistics(self, current_user: Any) -> StatisticsResult:
        if not PermissionChecker.is_publisher(current_user):
            return StatisticsResult(False, PERMISSION_DENIED_MESSAGE)

        activities = self._activity_repository.list_by_publisher(current_user.id)
        activity_ids = {activity.id for activity in activities}
        registrations = [
            registration
            for activity_id in activity_ids
            for registration in self._registration_repository.list_by_activity(activity_id)
            if registration.status in ACTIVE_REGISTRATION_STATUSES
        ]
        checkins = [
            checkin
            for activity_id in activity_ids
            for checkin in self._checkin_repository.list_by_activity(activity_id)
            if checkin.status in VALID_CHECKIN_STATUSES
        ]
        reviews = [
            review
            for activity_id in activity_ids
            for review in self._review_repository.list_by_activity(activity_id)
            if review.status == "visible"
        ]
        average_checkin_rate = len(checkins) / len(registrations) if registrations else 0.0
        average_score = sum(review.overall_score for review in reviews) / len(reviews) if reviews else 0.0

        return StatisticsResult(
            True,
            "查询成功。",
            publisher_statistics=PublisherStatisticsDTO(
                activity_count=len(activities),
                total_registrations=len(registrations),
                total_checkins=len(checkins),
                average_checkin_rate=average_checkin_rate,
                average_score=average_score,
            ),
        )

    def get_participant_statistics(self, current_user: Any) -> StatisticsResult:
        if not PermissionChecker.is_participant(current_user):
            return StatisticsResult(False, PERMISSION_DENIED_MESSAGE)

        registrations = [
            registration
            for registration in self._registration_repository.list_by_user(current_user.id)
            if registration.status in ACTIVE_REGISTRATION_STATUSES
        ]
        checkins = [
            checkin
            for checkin in self._checkin_repository.list_by_user(current_user.id)
            if checkin.status in VALID_CHECKIN_STATUSES
        ]
        reviews = [
            review
            for review in self._review_repository.list_by_user(current_user.id)
            if review.status == "visible"
        ]
        certificates = self._certificate_repository.list_by_user(current_user.id)
        checked_activity_ids = {checkin.activity_id for checkin in checkins}
        checked_activities = [
            activity
            for activity in (self._activity_repository.find_by_id(activity_id) for activity_id in checked_activity_ids)
            if activity is not None
        ]

        return StatisticsResult(
            True,
            "查询成功。",
            participant_statistics=ParticipantStatisticsDTO(
                registration_count=len(registrations),
                checkin_count=len(checkins),
                review_count=len(reviews),
                certificate_count=len(certificates),
                earned_credit=sum(activity.credit for activity in checked_activities),
                volunteer_hours=sum(activity.volunteer_hours for activity in checked_activities),
            ),
        )

    def list_publisher_calendar_events(self, current_user: Any) -> StatisticsResult:
        if not PermissionChecker.is_publisher(current_user):
            return StatisticsResult(False, PERMISSION_DENIED_MESSAGE)
        activities = self._activity_repository.list_by_publisher(current_user.id)
        return StatisticsResult(True, "查询成功。", calendar_events=[self._to_calendar_event(item) for item in activities])

    def list_participant_calendar_events(self, current_user: Any) -> StatisticsResult:
        if not PermissionChecker.is_participant(current_user):
            return StatisticsResult(False, PERMISSION_DENIED_MESSAGE)
        registrations = [
            registration
            for registration in self._registration_repository.list_by_user(current_user.id)
            if registration.status in ACTIVE_REGISTRATION_STATUSES
        ]
        activities = [registration.activity for registration in registrations if registration.activity is not None]
        return StatisticsResult(True, "查询成功。", calendar_events=[self._to_calendar_event(item) for item in activities])

    def _to_hot_activity(self, activity: Activity) -> HotActivityDTO:
        return HotActivityDTO(
            activity_id=activity.id,
            title=activity.title,
            category_name=activity.category.name if activity.category else "",
            publisher_name=activity.publisher.name if activity.publisher else "",
            registration_count=len(
                [
                    registration
                    for registration in self._registration_repository.list_by_activity(activity.id)
                    if registration.status in ACTIVE_REGISTRATION_STATUSES
                ]
            ),
            checkin_count=len(
                [
                    checkin
                    for checkin in self._checkin_repository.list_by_activity(activity.id)
                    if checkin.status in VALID_CHECKIN_STATUSES
                ]
            ),
        )

    def _to_calendar_event(self, activity: Activity) -> ActivityCalendarEventDTO:
        return ActivityCalendarEventDTO(
            activity_id=activity.id,
            title=activity.title,
            start_time=activity.start_time,
            end_time=activity.end_time,
            location=activity.location,
            status=activity.status,
        )
