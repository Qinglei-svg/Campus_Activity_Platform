from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from models.activity_model import Activity, ActivityCategory
from repositories.interfaces.activity_category_repository import IActivityCategoryRepository
from repositories.interfaces.activity_repository import IActivityRepository
from services.interfaces.activity_service import (
    ActivityCategoryDTO,
    ActivityDTO,
    ActivityResult,
    IActivityService,
)
from services.interfaces.notification_service import INotificationService
from utils.datetime_utils import current_datetime
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


EDITABLE_ACTIVITY_STATUSES = {"draft", "rejected"}


class ActivityServiceImpl(IActivityService):
    def __init__(
        self,
        activity_repository: IActivityRepository,
        category_repository: IActivityCategoryRepository,
        session: Session | None = None,
        notification_service: INotificationService | None = None,
    ) -> None:
        self._activity_repository = activity_repository
        self._category_repository = category_repository
        self._session = session
        self._notification_service = notification_service

    def list_online_activities(self, filters: dict[str, Any] | None = None) -> ActivityResult:
        filters = filters or {}
        keyword = filters.get("keyword") or None
        category_id = filters.get("category_id") or None
        if category_id in ("", 0):
            category_id = None

        activities = self._activity_repository.search_online(
            keyword=keyword,
            category_id=category_id,
            status="online",
        )
        return ActivityResult(
            True,
            "查询成功。",
            activities=[self._to_activity_dto(activity) for activity in activities],
        )

    def get_activity_detail(self, activity_id: int, current_user: Any | None = None) -> ActivityResult:
        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return ActivityResult(False, "活动不存在。")

        if activity.status != "online" and not self._can_access_non_online_activity(current_user, activity):
            return ActivityResult(False, "活动不存在或不可访问。")

        return ActivityResult(True, "查询成功。", activity=self._to_activity_dto(activity))

    def list_categories(self) -> ActivityResult:
        categories = self._category_repository.list_enabled_categories()
        return ActivityResult(
            True,
            "查询成功。",
            categories=[self._to_category_dto(category) for category in categories],
        )

    def create_draft(self, current_user: Any, data: dict[str, Any]) -> ActivityResult:
        if not PermissionChecker.is_publisher(current_user):
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)

        validation_message = self._validate_activity_data(data)
        if validation_message:
            return ActivityResult(False, validation_message)

        title = str(data["title"]).strip()
        if self._activity_repository.exists_title_by_publisher(current_user.id, title):
            return ActivityResult(False, "当前发布者已存在同名活动。")

        activity = Activity(
            publisher_id=current_user.id,
            category_id=int(data["category_id"]),
            title=title,
            cover_image="",
            description=str(data["description"]).strip(),
            start_time=data["start_time"],
            end_time=data["end_time"],
            signup_start_time=data["signup_start_time"],
            signup_end_time=data["signup_end_time"],
            location=str(data["location"]).strip(),
            capacity=int(data["capacity"]),
            signup_condition=str(data.get("signup_condition") or ""),
            need_signup_audit=bool(data.get("need_signup_audit", False)),
            credit=float(data.get("credit") or 0),
            volunteer_hours=float(data.get("volunteer_hours") or 0),
            status="draft",
            checkin_code=str(data.get("checkin_code") or ""),
            checkin_method="code",
            checkin_open=False,
            reject_reason="",
        )
        self._activity_repository.save(activity)
        self._commit()
        return ActivityResult(True, "草稿保存成功。", activity=self._to_activity_dto(activity))

    def update_activity(self, current_user: Any, activity_id: int, data: dict[str, Any]) -> ActivityResult:
        if not PermissionChecker.is_publisher(current_user):
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)

        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return ActivityResult(False, "活动不存在。")
        if activity.publisher_id != current_user.id:
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)
        if activity.status not in EDITABLE_ACTIVITY_STATUSES:
            return ActivityResult(False, "当前活动状态不允许编辑。")

        validation_message = self._validate_activity_data(data)
        if validation_message:
            return ActivityResult(False, validation_message)

        title = str(data["title"]).strip()
        if self._activity_repository.exists_title_by_publisher(current_user.id, title, exclude_activity_id=activity_id):
            return ActivityResult(False, "当前发布者已存在同名活动。")

        self._apply_activity_data(activity, data)
        activity.updated_at = current_datetime()
        self._activity_repository.update(activity)
        self._commit()
        return ActivityResult(True, "活动保存成功。", activity=self._to_activity_dto(activity))

    def submit_activity(self, current_user: Any, activity_id: int) -> ActivityResult:
        if not PermissionChecker.is_publisher(current_user):
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)

        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return ActivityResult(False, "活动不存在。")
        if activity.publisher_id != current_user.id:
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)
        if activity.status not in EDITABLE_ACTIVITY_STATUSES:
            return ActivityResult(False, "当前活动状态不允许提交审核。")

        activity.status = "pending_review"
        activity.reject_reason = ""
        activity.updated_at = current_datetime()
        self._activity_repository.update(activity)

        if self._notification_service is not None:
            self._notification_service.send_to_role(
                "admin",
                "有新的活动待审核",
                f"发布者【{current_user.name}】提交了活动【{activity.title}】，请及时审核。",
                "activity_review",
            )
        else:
            self._commit()

        return ActivityResult(True, "活动已提交审核。", activity=self._to_activity_dto(activity))

    def list_my_activities(self, current_user: Any, status: str | None = None) -> ActivityResult:
        if not PermissionChecker.is_publisher(current_user):
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)

        if status:
            activities = self._activity_repository.list_by_publisher_and_status(current_user.id, status)
        else:
            activities = self._activity_repository.list_by_publisher(current_user.id)
        return ActivityResult(
            True,
            "查询成功。",
            activities=[self._to_activity_dto(activity) for activity in activities],
        )

    def get_my_activity_detail(self, current_user: Any, activity_id: int) -> ActivityResult:
        if not PermissionChecker.is_publisher(current_user):
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)

        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return ActivityResult(False, "活动不存在。")
        if activity.publisher_id != current_user.id:
            return ActivityResult(False, PERMISSION_DENIED_MESSAGE)
        return ActivityResult(True, "查询成功。", activity=self._to_activity_dto(activity))

    def _validate_activity_data(self, data: dict[str, Any]) -> str | None:
        if not str(data.get("title") or "").strip():
            return "活动标题不能为空。"
        category_id = data.get("category_id")
        if category_id in (None, "", 0):
            return "活动分类不能为空。"
        category = self._category_repository.find_by_id(int(category_id))
        if category is None or not category.enabled:
            return "活动分类不存在或已禁用。"
        if not str(data.get("location") or "").strip():
            return "活动地点不能为空。"

        try:
            capacity = int(data.get("capacity"))
        except (TypeError, ValueError):
            return "活动容量必须是正整数。"
        if capacity <= 0:
            return "活动容量必须是正整数。"

        try:
            credit = float(data.get("credit") or 0)
            volunteer_hours = float(data.get("volunteer_hours") or 0)
        except (TypeError, ValueError):
            return "学分和志愿时长必须是数字。"
        if credit < 0:
            return "学分不能小于 0。"
        if volunteer_hours < 0:
            return "志愿时长不能小于 0。"

        start_time = data.get("start_time")
        end_time = data.get("end_time")
        signup_start_time = data.get("signup_start_time")
        signup_end_time = data.get("signup_end_time")
        if not all(isinstance(value, datetime) for value in (start_time, end_time, signup_start_time, signup_end_time)):
            return "活动时间和报名时间不能为空。"
        if start_time > end_time:
            return "活动开始时间不能晚于结束时间。"
        if signup_start_time > signup_end_time:
            return "报名开始时间不能晚于报名结束时间。"
        if signup_end_time > end_time:
            return "报名结束时间不能晚于活动结束时间。"

        if not str(data.get("description") or "").strip():
            return "活动详情不能为空。"

        return None

    def _apply_activity_data(self, activity: Activity, data: dict[str, Any]) -> None:
        activity.title = str(data["title"]).strip()
        activity.category_id = int(data["category_id"])
        activity.description = str(data["description"]).strip()
        activity.start_time = data["start_time"]
        activity.end_time = data["end_time"]
        activity.signup_start_time = data["signup_start_time"]
        activity.signup_end_time = data["signup_end_time"]
        activity.location = str(data["location"]).strip()
        activity.capacity = int(data["capacity"])
        activity.signup_condition = str(data.get("signup_condition") or "")
        activity.need_signup_audit = bool(data.get("need_signup_audit", False))
        activity.credit = float(data.get("credit") or 0)
        activity.volunteer_hours = float(data.get("volunteer_hours") or 0)

    def _can_access_non_online_activity(self, current_user: Any | None, activity: Activity) -> bool:
        if current_user is None:
            return False
        return PermissionChecker.is_admin(current_user) or PermissionChecker.can_manage_activity(current_user, activity)

    def _to_activity_dto(self, activity: Activity) -> ActivityDTO:
        registered_count = self._activity_repository.count_registered(activity.id)
        remaining_count = max(activity.capacity - registered_count, 0)
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
            remaining_count=remaining_count,
            credit=activity.credit,
            volunteer_hours=activity.volunteer_hours,
            status=activity.status,
            description=activity.description,
            need_signup_audit=activity.need_signup_audit,
            reject_reason=activity.reject_reason,
            updated_at=activity.updated_at,
        )

    def _to_category_dto(self, category: ActivityCategory) -> ActivityCategoryDTO:
        return ActivityCategoryDTO(
            category_id=category.id,
            name=category.name,
            description=category.description,
        )

    def _commit(self) -> None:
        if self._session is not None:
            self._session.commit()
