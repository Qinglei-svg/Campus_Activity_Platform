from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from models.registration_model import Registration
from repositories.interfaces.activity_repository import IActivityRepository
from repositories.interfaces.registration_repository import IRegistrationRepository
from services.interfaces.registration_service import RegistrationDTO, RegistrationResult, IRegistrationService
from utils.datetime_utils import current_datetime
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


ACTIVE_REGISTRATION_STATUSES = {"registered", "waiting", "approved", "checked_in"}


class RegistrationServiceImpl(IRegistrationService):
    def __init__(
        self,
        session: Session,
        activity_repository: IActivityRepository,
        registration_repository: IRegistrationRepository,
    ) -> None:
        self._session = session
        self._activity_repository = activity_repository
        self._registration_repository = registration_repository

    def register_activity(self, current_user, activity_id: int) -> RegistrationResult:
        if not PermissionChecker.is_participant(current_user):
            return RegistrationResult(False, PERMISSION_DENIED_MESSAGE)

        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return RegistrationResult(False, "活动不存在。")
        if activity.status != "online":
            return RegistrationResult(False, "当前活动不可报名。")

        now = current_datetime()
        if now < activity.signup_start_time:
            return RegistrationResult(False, "报名尚未开始。")
        if now > activity.signup_end_time:
            return RegistrationResult(False, "报名已结束。")

        existing = self._registration_repository.find_by_activity_and_user(activity_id, current_user.id)
        if existing is not None and existing.status in ACTIVE_REGISTRATION_STATUSES:
            return RegistrationResult(False, "你已报名该活动，请勿重复报名。")

        registered_count = self._registration_repository.count_registered(activity_id)
        status = "registered" if registered_count < activity.capacity else "waiting"
        waiting_order = None
        if status == "waiting":
            waiting_order = self._registration_repository.count_waiting(activity_id) + 1

        if existing is None:
            registration = Registration(
                activity_id=activity_id,
                user_id=current_user.id,
                status=status,
                waiting_order=waiting_order,
                registration_code=self._generate_registration_code(),
                registered_at=now,
                canceled_at=None,
            )
            self._registration_repository.save(registration)
        else:
            existing.status = status
            existing.waiting_order = waiting_order
            existing.registered_at = now
            existing.canceled_at = None
            registration = self._registration_repository.update(existing)

        self._session.commit()
        registration = self._registration_repository.find_by_id(registration.id)
        message = "报名成功。" if status == "registered" else "活动名额已满，已加入候补。"
        return RegistrationResult(True, message, registration=self._to_dto(registration))

    def cancel_registration(self, current_user, registration_id: int) -> RegistrationResult:
        if not PermissionChecker.is_participant(current_user):
            return RegistrationResult(False, PERMISSION_DENIED_MESSAGE)

        registration = self._registration_repository.find_by_id(registration_id)
        if registration is None:
            return RegistrationResult(False, "报名记录不存在。")
        if registration.user_id != current_user.id:
            return RegistrationResult(False, PERMISSION_DENIED_MESSAGE)
        if registration.status == "canceled":
            return RegistrationResult(False, "报名已取消，请勿重复操作。")

        was_registered = registration.status in {"registered", "approved", "checked_in"}
        registration.status = "canceled"
        registration.waiting_order = None
        registration.canceled_at = current_datetime()
        self._registration_repository.update(registration)

        promoted = None
        if was_registered:
            promoted = self._registration_repository.find_first_waiting(registration.activity_id)
            if promoted is not None:
                promoted.status = "registered"
                promoted.waiting_order = None
                self._registration_repository.update(promoted)

        self._session.commit()
        canceled = self._registration_repository.find_by_id(registration.id)
        promoted_dto = self._to_dto(promoted) if promoted is not None else None
        return RegistrationResult(
            True,
            "取消报名成功。",
            registration=self._to_dto(canceled),
            promoted_registration=promoted_dto,
        )

    def list_my_registrations(self, current_user) -> RegistrationResult:
        if not PermissionChecker.is_participant(current_user):
            return RegistrationResult(False, PERMISSION_DENIED_MESSAGE)
        registrations = self._registration_repository.list_by_user(current_user.id)
        return RegistrationResult(
            True,
            "查询成功。",
            registrations=[self._to_dto(registration) for registration in registrations],
        )

    def list_activity_registrations(self, current_user, activity_id: int) -> RegistrationResult:
        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return RegistrationResult(False, "活动不存在。")
        if not PermissionChecker.can_manage_activity(current_user, activity):
            return RegistrationResult(False, PERMISSION_DENIED_MESSAGE)

        registrations = self._registration_repository.list_by_activity(activity_id)
        return RegistrationResult(
            True,
            "查询成功。",
            registrations=[self._to_dto(registration) for registration in registrations],
        )

    def _to_dto(self, registration: Registration) -> RegistrationDTO:
        activity = registration.activity
        return RegistrationDTO(
            registration_id=registration.id,
            activity_id=registration.activity_id,
            activity_title=activity.title if activity else "",
            category_name=activity.category.name if activity and activity.category else "",
            publisher_name=activity.publisher.name if activity and activity.publisher else "",
            user_id=registration.user_id,
            status=registration.status,
            waiting_order=registration.waiting_order,
            registration_code=registration.registration_code,
            registered_at=registration.registered_at,
            canceled_at=registration.canceled_at,
            start_time=activity.start_time if activity else current_datetime(),
            end_time=activity.end_time if activity else current_datetime(),
            location=activity.location if activity else "",
            user_account=registration.user.account if registration.user else "",
            user_name=registration.user.name if registration.user else "",
        )

    def _generate_registration_code(self) -> str:
        return f"REG-{uuid4().hex[:12].upper()}"
