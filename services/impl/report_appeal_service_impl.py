from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from models.audit_log_model import AuditLog
from models.report_appeal_model import ReportAppeal
from models.user_model import User
from repositories.interfaces.activity_repository import IActivityRepository
from repositories.interfaces.audit_log_repository import IAuditLogRepository
from repositories.interfaces.report_appeal_repository import IReportAppealRepository
from repositories.interfaces.user_repository import IUserRepository
from services.interfaces.notification_service import INotificationService
from services.interfaces.report_appeal_service import (
    ReportAppealDTO,
    ReportAppealResult,
    IReportAppealService,
)
from utils.datetime_utils import current_datetime
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


class ReportAppealServiceImpl(IReportAppealService):
    def __init__(
        self,
        session: Session,
        report_repository: IReportAppealRepository,
        user_repository: IUserRepository,
        activity_repository: IActivityRepository,
        audit_log_repository: IAuditLogRepository,
        notification_service: INotificationService,
    ) -> None:
        self._session = session
        self._report_repository = report_repository
        self._user_repository = user_repository
        self._activity_repository = activity_repository
        self._audit_log_repository = audit_log_repository
        self._notification_service = notification_service

    def submit_activity_report(self, current_user: Any, activity_id: int, reason: str) -> ReportAppealResult:
        if not PermissionChecker.is_participant(current_user):
            return ReportAppealResult(False, "只有活动参与者可以举报活动。")
        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return ReportAppealResult(False, "活动不存在。")
        return self._create_report(current_user.id, "activity", activity_id, reason)

    def submit_publisher_report(self, current_user: Any, publisher_id: int, reason: str) -> ReportAppealResult:
        if not PermissionChecker.is_participant(current_user):
            return ReportAppealResult(False, "只有活动参与者可以举报发布者。")
        publisher = self._user_repository.find_by_id(publisher_id)
        if publisher is None or not PermissionChecker.is_publisher(publisher):
            return ReportAppealResult(False, "发布者不存在。")
        return self._create_report(current_user.id, "publisher", publisher_id, reason)

    def submit_participant_report(self, current_user: Any, participant_id: int, reason: str) -> ReportAppealResult:
        if not PermissionChecker.is_publisher(current_user):
            return ReportAppealResult(False, "只有活动发布者可以举报参与者。")
        participant = self._user_repository.find_by_id(participant_id)
        if participant is None or not PermissionChecker.is_participant(participant):
            return ReportAppealResult(False, "参与者不存在。")
        return self._create_report(current_user.id, "participant", participant_id, reason)

    def list_my_reports(self, current_user: Any) -> ReportAppealResult:
        if current_user is None:
            return ReportAppealResult(False, PERMISSION_DENIED_MESSAGE)
        reports = self._report_repository.list_by_submitter(current_user.id)
        return ReportAppealResult(True, "查询成功。", reports=[self._to_dto(report) for report in reports])

    def list_reports(self, admin_user: Any, status: str | None = None) -> ReportAppealResult:
        if not PermissionChecker.is_admin(admin_user):
            return ReportAppealResult(False, PERMISSION_DENIED_MESSAGE)
        reports = self._report_repository.list_by_status(status) if status else self._report_repository.list_all()
        return ReportAppealResult(True, "查询成功。", reports=[self._to_dto(report) for report in reports])

    def punish_report(self, admin_user: Any, report_id: int) -> ReportAppealResult:
        if not PermissionChecker.is_admin(admin_user):
            return ReportAppealResult(False, PERMISSION_DENIED_MESSAGE)
        report = self._report_repository.find_by_id(report_id)
        if report is None:
            return ReportAppealResult(False, "举报记录不存在。")
        if report.status != "pending":
            return ReportAppealResult(False, "该举报已处理。")

        target_user = self._resolve_target_user(report)
        if target_user is None:
            return ReportAppealResult(False, "举报目标用户不存在。")
        if target_user.id == admin_user.id:
            return ReportAppealResult(False, "不能处罚当前登录管理员。")

        frozen_until = current_datetime() + timedelta(days=1)
        target_user.status = "frozen"
        target_user.frozen_until = frozen_until
        target_user.violation_count += 1
        target_user.updated_at = current_datetime()

        report.status = "punished"
        report.result = f"已处罚：目标用户禁止登录至 {frozen_until.strftime('%Y-%m-%d %H:%M')}。"
        report.handler_id = admin_user.id
        report.handled_at = current_datetime()

        self._user_repository.update(target_user)
        self._report_repository.update(report)
        self._write_audit_log(admin_user.id, "report_appeal", report.id, "punish", "punished", report.result)
        self._session.commit()

        self._notification_service.send_to_user(
            report.submitter_id,
            "举报处理结果",
            f"你提交的举报已处理，处理结果：{report.result}",
            "report_appeal",
        )
        self._notification_service.send_to_user(
            target_user.id,
            "账号处罚通知",
            f"因举报处理结果，你的账号已被禁止登录至 {frozen_until.strftime('%Y-%m-%d %H:%M')}。",
            "report_appeal",
        )
        report = self._report_repository.find_by_id(report.id)
        return ReportAppealResult(True, "已完成处罚。", report=self._to_dto(report))

    def ignore_report(self, admin_user: Any, report_id: int, result: str) -> ReportAppealResult:
        if not PermissionChecker.is_admin(admin_user):
            return ReportAppealResult(False, PERMISSION_DENIED_MESSAGE)
        report = self._report_repository.find_by_id(report_id)
        if report is None:
            return ReportAppealResult(False, "举报记录不存在。")
        if report.status != "pending":
            return ReportAppealResult(False, "该举报已处理。")

        cleaned_result = str(result or "").strip() or "管理员核查后决定不做处理。"
        report.status = "ignored"
        report.result = cleaned_result
        report.handler_id = admin_user.id
        report.handled_at = current_datetime()
        self._report_repository.update(report)
        self._write_audit_log(admin_user.id, "report_appeal", report.id, "ignore", "ignored", cleaned_result)
        self._session.commit()

        self._notification_service.send_to_user(
            report.submitter_id,
            "举报处理结果",
            f"你提交的举报已处理，处理结果：{cleaned_result}",
            "report_appeal",
        )
        report = self._report_repository.find_by_id(report.id)
        return ReportAppealResult(True, "已标记为不做处理。", report=self._to_dto(report))

    def _create_report(self, submitter_id: int, target_type: str, target_id: int, reason: str) -> ReportAppealResult:
        cleaned_reason = str(reason or "").strip()
        if not cleaned_reason:
            return ReportAppealResult(False, "举报原因不能为空。")

        report = ReportAppeal(
            submitter_id=submitter_id,
            target_type=target_type,
            target_id=target_id,
            reason=cleaned_reason,
            evidence_file="",
            status="pending",
            result="",
        )
        self._report_repository.save(report)
        self._session.commit()
        report = self._report_repository.find_by_id(report.id)
        dto = self._to_dto(report)
        self._notification_service.send_to_role(
            "admin",
            "收到新的举报申诉",
            f"用户【{dto.submitter_name}】提交了举报，举报对象：{dto.target_name}，请及时处理。",
            "report_appeal",
        )
        return ReportAppealResult(True, "举报已提交，请等待管理员处理。", report=dto)

    def _resolve_target_user(self, report: ReportAppeal) -> User | None:
        if report.target_type in {"publisher", "participant"}:
            return self._user_repository.find_by_id(report.target_id)
        if report.target_type == "activity":
            activity = self._activity_repository.find_by_id(report.target_id)
            if activity is None:
                return None
            return self._user_repository.find_by_id(activity.publisher_id)
        return None

    def _target_name(self, report: ReportAppeal) -> str:
        if report.target_type == "activity":
            activity = self._activity_repository.find_by_id(report.target_id)
            return f"活动：{activity.title}" if activity is not None else "活动：已不存在"
        user = self._user_repository.find_by_id(report.target_id)
        if user is None:
            return "用户：已不存在"
        label = "发布者" if report.target_type == "publisher" else "参与者"
        return f"{label}：{user.name}（{user.account}）"

    def _target_user_id(self, report: ReportAppeal) -> int | None:
        user = self._resolve_target_user(report)
        return user.id if user is not None else None

    def _write_audit_log(self, operator_id: int, target_type: str, target_id: int, action: str, result: str, reason: str) -> None:
        self._audit_log_repository.save(
            AuditLog(
                operator_id=operator_id,
                target_type=target_type,
                target_id=target_id,
                action=action,
                result=result,
                reason=reason,
            )
        )

    def _to_dto(self, report: ReportAppeal) -> ReportAppealDTO:
        return ReportAppealDTO(
            report_id=report.id,
            submitter_id=report.submitter_id,
            submitter_account=report.submitter.account if report.submitter else "",
            submitter_name=report.submitter.name if report.submitter else "",
            submitter_role_name=report.submitter.role.name if report.submitter and report.submitter.role else "",
            target_type=report.target_type,
            target_id=report.target_id,
            target_name=self._target_name(report),
            target_user_id=self._target_user_id(report),
            reason=report.reason,
            evidence_file=report.evidence_file,
            status=report.status,
            result=report.result,
            handler_name=report.handler.name if report.handler else "",
            submitted_at=report.submitted_at,
            handled_at=report.handled_at,
        )
