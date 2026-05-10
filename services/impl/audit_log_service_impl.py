from __future__ import annotations

from typing import Any

from models.audit_log_model import AuditLog
from repositories.interfaces.audit_log_repository import IAuditLogRepository
from services.interfaces.audit_log_service import AuditLogDTO, AuditLogResult, IAuditLogService
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


ACTION_NAMES = {
    "approve": "活动审核通过",
    "reject": "活动审核驳回",
    "freeze": "冻结用户",
    "unfreeze": "解冻用户",
    "correct_checkin": "手动修正签到",
    "delete_review": "删除评价",
    "punish": "举报处罚",
    "ignore": "举报不做处理",
}


class AuditLogServiceImpl(IAuditLogService):
    def __init__(self, audit_log_repository: IAuditLogRepository) -> None:
        self._audit_log_repository = audit_log_repository

    def list_logs(
        self,
        admin_user: Any,
        action: str | None = None,
        operator_keyword: str | None = None,
    ) -> AuditLogResult:
        if not PermissionChecker.is_admin(admin_user):
            return AuditLogResult(False, PERMISSION_DENIED_MESSAGE)

        logs = self._audit_log_repository.list_all()
        if action:
            logs = [log for log in logs if log.action == action]
        keyword = str(operator_keyword or "").strip().lower()
        if keyword:
            logs = [
                log
                for log in logs
                if keyword in (log.operator.account if log.operator else "").lower()
                or keyword in (log.operator.name if log.operator else "").lower()
            ]

        return AuditLogResult(True, "查询成功。", logs=[self._to_dto(log) for log in logs])

    def list_action_options(self, admin_user: Any) -> AuditLogResult:
        if not PermissionChecker.is_admin(admin_user):
            return AuditLogResult(False, PERMISSION_DENIED_MESSAGE)
        actions = [(action, ACTION_NAMES[action]) for action in ACTION_NAMES]
        return AuditLogResult(True, "查询成功。", actions=actions)

    def _to_dto(self, log: AuditLog) -> AuditLogDTO:
        operator = log.operator
        return AuditLogDTO(
            log_id=log.id,
            operator_id=log.operator_id,
            operator_account=operator.account if operator else "",
            operator_name=operator.name if operator else "",
            operator_role_name=operator.role.name if operator and operator.role else "",
            target_type=log.target_type,
            target_id=log.target_id,
            action=log.action,
            action_name=ACTION_NAMES.get(log.action, log.action),
            result=log.result,
            reason=log.reason,
            operated_at=log.operated_at,
        )
