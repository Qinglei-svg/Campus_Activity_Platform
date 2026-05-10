from __future__ import annotations

from pathlib import Path

import qrcode
from sqlalchemy.orm import Session

from config.paths import UPLOADS_DIR
from models.audit_log_model import AuditLog
from models.checkin_model import CheckinRecord
from models.registration_model import Registration
from repositories.interfaces.activity_repository import IActivityRepository
from repositories.interfaces.audit_log_repository import IAuditLogRepository
from repositories.interfaces.checkin_repository import ICheckinRepository
from repositories.interfaces.registration_repository import IRegistrationRepository
from services.interfaces.checkin_service import CheckinRecordDTO, CheckinResult, ICheckinService
from services.interfaces.notification_service import INotificationService
from utils.datetime_utils import current_datetime
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


class CheckinServiceImpl(ICheckinService):
    def __init__(
        self,
        session: Session,
        activity_repository: IActivityRepository,
        registration_repository: IRegistrationRepository,
        checkin_repository: ICheckinRepository,
        audit_log_repository: IAuditLogRepository,
        notification_service: INotificationService,
    ) -> None:
        self._session = session
        self._activity_repository = activity_repository
        self._registration_repository = registration_repository
        self._checkin_repository = checkin_repository
        self._audit_log_repository = audit_log_repository
        self._notification_service = notification_service

    def enable_checkin(self, current_user, activity_id: int, method: str, code: str) -> CheckinResult:
        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return CheckinResult(False, "活动不存在。")
        if not PermissionChecker.is_publisher(current_user) or activity.publisher_id != current_user.id:
            return CheckinResult(False, PERMISSION_DENIED_MESSAGE)
        if method not in {"password", "qrcode"}:
            return CheckinResult(False, "签到方式不正确。")
        code = code.strip()
        if not code:
            return CheckinResult(False, "签到口令不能为空。")

        activity.checkin_open = True
        activity.checkin_method = method
        activity.checkin_code = code
        activity.updated_at = current_datetime()
        self._activity_repository.update(activity)
        qr_path = self._generate_qr_code(activity.id, code) if method == "qrcode" else None
        self._session.commit()
        return CheckinResult(True, "签到已开启。", qr_code_path=qr_path)

    def participant_checkin(self, current_user, activity_id: int, code: str) -> CheckinResult:
        if not PermissionChecker.is_participant(current_user):
            return CheckinResult(False, PERMISSION_DENIED_MESSAGE)

        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return CheckinResult(False, "活动不存在。")
        if not activity.checkin_open:
            return CheckinResult(False, "签到尚未开启。")
        if code.strip() not in {activity.checkin_code, f"{activity.id}:{activity.checkin_code}"}:
            return CheckinResult(False, "签到口令错误。")

        registration = self._registration_repository.find_by_activity_and_user(activity_id, current_user.id)
        if registration is None or registration.status != "registered":
            return CheckinResult(False, "只有已报名用户可以签到。")
        existing = self._checkin_repository.find_by_registration(registration.id)
        if existing is not None:
            return CheckinResult(False, "你已完成签到，请勿重复签到。")

        checkin = CheckinRecord(
            activity_id=activity_id,
            user_id=current_user.id,
            registration_id=registration.id,
            checkin_method=activity.checkin_method,
            status="checked_in",
            location_info="",
            operator_type="user",
            operator_id=current_user.id,
            correction_reason="",
        )
        self._checkin_repository.save(checkin)
        self._notification_service.send_to_user(
            current_user.id,
            "签到成功",
            f"你已成功签到活动【{activity.title}】。",
            "checkin",
        )
        checkin = self._checkin_repository.find_by_id(checkin.id)
        return CheckinResult(True, "签到成功。", checkin=self._to_dto(checkin))

    def list_activity_checkins(self, current_user, activity_id: int) -> CheckinResult:
        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return CheckinResult(False, "活动不存在。")
        if not PermissionChecker.is_publisher(current_user) or activity.publisher_id != current_user.id:
            return CheckinResult(False, PERMISSION_DENIED_MESSAGE)

        registrations = self._registration_repository.list_by_activity(activity_id)
        return CheckinResult(True, "查询成功。", checkins=[self._registration_to_dto(item) for item in registrations])

    def list_my_checkins(self, current_user) -> CheckinResult:
        if not PermissionChecker.is_participant(current_user):
            return CheckinResult(False, PERMISSION_DENIED_MESSAGE)
        records = self._checkin_repository.list_by_user(current_user.id)
        return CheckinResult(True, "查询成功。", checkins=[self._to_dto(record) for record in records])

    def correct_checkin(self, current_user, registration_id: int, status: str, reason: str) -> CheckinResult:
        reason = reason.strip()
        if not reason:
            return CheckinResult(False, "修正原因不能为空。")
        if status not in {"checked_in", "absent", "corrected"}:
            return CheckinResult(False, "签到状态不正确。")

        registration = self._registration_repository.find_by_id(registration_id)
        if registration is None:
            return CheckinResult(False, "报名记录不存在。")
        activity = registration.activity
        if not PermissionChecker.is_publisher(current_user) or activity.publisher_id != current_user.id:
            return CheckinResult(False, PERMISSION_DENIED_MESSAGE)

        checkin = self._checkin_repository.find_by_registration(registration_id)
        if checkin is None:
            checkin = CheckinRecord(
                activity_id=registration.activity_id,
                user_id=registration.user_id,
                registration_id=registration.id,
                checkin_method="manual",
                status=status,
                location_info="",
                operator_type="publisher",
                operator_id=current_user.id,
                correction_reason=reason,
            )
            self._checkin_repository.save(checkin)
        else:
            checkin.status = status
            checkin.operator_type = "publisher"
            checkin.operator_id = current_user.id
            checkin.correction_reason = reason
            checkin.checkin_time = current_datetime()
            self._checkin_repository.update(checkin)

        self._audit_log_repository.save(
            AuditLog(
                operator_id=current_user.id,
                target_type="checkin_record",
                target_id=checkin.id,
                action="correct_checkin",
                result=status,
                reason=reason,
            )
        )
        self._session.commit()
        checkin = self._checkin_repository.find_by_id(checkin.id)
        return CheckinResult(True, "签到修正成功。", checkin=self._to_dto(checkin))

    def _generate_qr_code(self, activity_id: int, code: str) -> Path:
        qr_dir = UPLOADS_DIR / "qrcodes"
        qr_dir.mkdir(parents=True, exist_ok=True)
        qr_path = qr_dir / f"activity_{activity_id}_checkin.png"
        image = qrcode.make(f"{activity_id}:{code}")
        image.save(qr_path)
        return qr_path

    def _registration_to_dto(self, registration: Registration) -> CheckinRecordDTO:
        checkin = self._checkin_repository.find_by_registration(registration.id)
        if checkin is not None:
            return self._to_dto(checkin)
        activity = registration.activity
        user = registration.user
        return CheckinRecordDTO(
            checkin_id=None,
            activity_id=registration.activity_id,
            activity_title=activity.title if activity else "",
            user_id=registration.user_id,
            user_account=user.account if user else "",
            user_name=user.name if user else "",
            registration_id=registration.id,
            registration_status=registration.status,
            checkin_method="",
            status="not_checked_in",
            checkin_time=None,
            location_info="",
            correction_reason="",
        )

    def _to_dto(self, checkin: CheckinRecord) -> CheckinRecordDTO:
        activity = checkin.activity
        user = checkin.user
        registration = checkin.registration
        return CheckinRecordDTO(
            checkin_id=checkin.id,
            activity_id=checkin.activity_id,
            activity_title=activity.title if activity else "",
            user_id=checkin.user_id,
            user_account=user.account if user else "",
            user_name=user.name if user else "",
            registration_id=checkin.registration_id,
            registration_status=registration.status if registration else "",
            checkin_method=checkin.checkin_method,
            status=checkin.status,
            checkin_time=checkin.checkin_time,
            location_info=checkin.location_info,
            correction_reason=checkin.correction_reason,
        )
