from __future__ import annotations

from sqlalchemy.orm import Session

from models.activity_model import Activity
from models.audit_log_model import AuditLog
from repositories.interfaces.activity_repository import IActivityRepository
from repositories.interfaces.audit_log_repository import IAuditLogRepository
from services.interfaces.activity_service import ActivityDTO, ActivityResult
from services.interfaces.audit_service import IAuditService
from services.interfaces.notification_service import INotificationService
from utils.datetime_utils import current_datetime
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


class AuditServiceImpl(IAuditService):
    def __init__(
        self,
        session: Session,
        activity_repository: IActivityRepository,
        audit_log_repository: IAuditLogRepository,
        notification_service: INotificationService,
    ) -> None:
        self._session = session
        self._activity_repository = activity_repository
        self._audit_log_repository = audit_log_repository
        self._notification_service = notification_service

    def list_pending_activities(self, current_user) -> ActivityResult:
        if not PermissionChecker.is_admin(current_user):
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)

        activities = sorted(
            self._activity_repository.list_by_status("pending_review"),
            key=lambda activity: activity.updated_at,
            reverse=True,
        )
        return ActivityResult(
            True,
            "查询成功。",
            activities=[self._to_activity_dto(activity) for activity in activities],
        )

    def approve_activity(self, current_user, activity_id: int) -> ActivityResult:
        if not PermissionChecker.is_admin(current_user):
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)

        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return ActivityResult(False, "活动不存在。")
        if activity.status != "pending_review":
            return ActivityResult(False, "当前活动状态不允许审核。")

        activity.status = "online"
        activity.updated_at = current_datetime()
        self._activity_repository.update(activity)
        self._write_audit_log(current_user.id, activity.id, "approve", "approved", "")
        self._notification_service.send_to_user(
            activity.publisher_id,
            "活动审核通过",
            f"你的活动【{activity.title}】已审核通过并上线。",
            "activity_audit",
        )
        return ActivityResult(True, "活动审核通过。", activity=self._to_activity_dto(activity))

    def reject_activity(self, current_user, activity_id: int, reason: str) -> ActivityResult:
        if not PermissionChecker.is_admin(current_user):
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)

        reason = reason.strip()
        if not reason:
            return ActivityResult(False, "驳回原因不能为空。")

        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return ActivityResult(False, "活动不存在。")
        if activity.status != "pending_review":
            return ActivityResult(False, "当前活动状态不允许审核。")

        activity.status = "rejected"
        activity.reject_reason = reason
        activity.updated_at = current_datetime()
        self._activity_repository.update(activity)
        self._write_audit_log(current_user.id, activity.id, "reject", "rejected", reason)
        self._notification_service.send_to_user(
            activity.publisher_id,
            "活动审核未通过",
            f"你的活动【{activity.title}】审核未通过，原因：【{reason}】。",
            "activity_audit",
        )
        return ActivityResult(True, "活动已驳回。", activity=self._to_activity_dto(activity))

    def _write_audit_log(
        self,
        operator_id: int,
        activity_id: int,
        action: str,
        result: str,
        reason: str,
    ) -> None:
        self._audit_log_repository.save(
            AuditLog(
                operator_id=operator_id,
                target_type="activity",
                target_id=activity_id,
                action=action,
                result=result,
                reason=reason,
            )
        )

    def _to_activity_dto(self, activity: Activity) -> ActivityDTO:
        registered_count = self._activity_repository.count_registered(activity.id)
        return ActivityDTO(
            activity_id=activity.id,
            title=activity.title,
            category_id=activity.category_id,
            category_name=activity.category.name if activity.category else "",
            publisher_id=activity.publisher_id,
            publisher_name=activity.publisher.name if activity.publisher else "",
            start_time=activity.start_time,
            end_time=activity.end_time,
            signup_start_time=activity.signup_start_time,
            signup_end_time=activity.signup_end_time,
            location=activity.location,
            capacity=activity.capacity,
            registered_count=registered_count,
            remaining_count=max(activity.capacity - registered_count, 0),
            credit=activity.credit,
            volunteer_hours=activity.volunteer_hours,
            status=activity.status,
            description=activity.description,
            need_signup_audit=activity.need_signup_audit,
            reject_reason=activity.reject_reason,
            updated_at=activity.updated_at,
        )
