from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.audit_log_model import AuditLog
from models.user_model import PublisherApplication
from repositories.interfaces.audit_log_repository import IAuditLogRepository
from repositories.interfaces.role_repository import IRoleRepository
from repositories.interfaces.user_repository import IUserRepository
from services.interfaces.notification_service import INotificationService
from services.interfaces.user_service import PublisherApplicationDTO, UserDTO, UserResult, IUserService
from utils.datetime_utils import current_datetime
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


class UserServiceImpl(IUserService):
    def __init__(
        self,
        session: Session,
        user_repository: IUserRepository,
        role_repository: IRoleRepository,
        audit_log_repository: IAuditLogRepository,
        notification_service: INotificationService,
    ) -> None:
        self._session = session
        self._user_repository = user_repository
        self._role_repository = role_repository
        self._audit_log_repository = audit_log_repository
        self._notification_service = notification_service

    def submit_publisher_application(self, user: Any, data: dict[str, Any]) -> UserResult:
        if not PermissionChecker.is_participant(user):
            return UserResult(False, "只有活动参与者可以申请成为发布者。")
        current_user = self._user_repository.find_by_id(user.id)
        if current_user is None:
            return UserResult(False, "用户不存在。")
        if self._user_repository.find_pending_publisher_application_by_user(user.id) is not None:
            return UserResult(False, "你已有待审核的发布者申请。")

        organization_name = str(data.get("organization_name") or "").strip()
        responsible_person = str(data.get("responsible_person") or "").strip()
        contact_info = str(data.get("contact_info") or "").strip()
        application_note = str(data.get("application_note") or "").strip()
        if not organization_name:
            return UserResult(False, "组织名称不能为空。")
        if not responsible_person:
            return UserResult(False, "负责人不能为空。")
        if not contact_info:
            return UserResult(False, "联系方式不能为空。")

        application = PublisherApplication(
            user_id=user.id,
            organization_name=organization_name,
            responsible_person=responsible_person,
            contact_info=contact_info,
            proof_file=application_note,
            status="pending",
            reject_reason="",
        )
        self._user_repository.save_publisher_application(application)
        self._session.commit()
        application = self._user_repository.find_publisher_application_by_id(application.id)
        return UserResult(True, "申请已提交，请等待管理员审核。", application=self._to_application_dto(application))

    def list_publisher_applications(self, admin_user: Any) -> UserResult:
        if not PermissionChecker.is_admin(admin_user):
            return UserResult(False, PERMISSION_DENIED_MESSAGE)
        applications = self._user_repository.list_publisher_applications()
        return UserResult(
            True,
            "查询成功。",
            applications=[self._to_application_dto(application) for application in applications],
        )

    def approve_publisher_application(self, admin_user: Any, application_id: int) -> UserResult:
        if not PermissionChecker.is_admin(admin_user):
            return UserResult(False, PERMISSION_DENIED_MESSAGE)
        application = self._user_repository.find_publisher_application_by_id(application_id)
        if application is None:
            return UserResult(False, "申请不存在。")
        if application.status != "pending":
            return UserResult(False, "该申请已处理。")
        publisher_role = self._role_repository.find_by_code("publisher")
        if publisher_role is None:
            return UserResult(False, "系统缺少发布者角色。")

        application.status = "approved"
        application.reviewed_at = current_datetime()
        application.reviewer_id = admin_user.id
        application.reject_reason = ""
        application.user.role_id = publisher_role.id
        application.user.auth_status = "approved"
        application.user.updated_at = current_datetime()
        self._user_repository.update_publisher_application(application)
        self._user_repository.update(application.user)
        self._write_audit_log(admin_user.id, "publisher_application", application.id, "approve", "approved", "")
        self._notification_service.send_to_user(
            application.user_id,
            "发布者申请审核通过",
            "你的发布者申请已审核通过，现在可以发布和管理活动。",
            "publisher_application",
        )
        application = self._user_repository.find_publisher_application_by_id(application.id)
        return UserResult(True, "申请已通过。", application=self._to_application_dto(application))

    def reject_publisher_application(self, admin_user: Any, application_id: int, reason: str) -> UserResult:
        if not PermissionChecker.is_admin(admin_user):
            return UserResult(False, PERMISSION_DENIED_MESSAGE)
        reason = reason.strip()
        if not reason:
            return UserResult(False, "驳回原因不能为空。")
        application = self._user_repository.find_publisher_application_by_id(application_id)
        if application is None:
            return UserResult(False, "申请不存在。")
        if application.status != "pending":
            return UserResult(False, "该申请已处理。")

        application.status = "rejected"
        application.reject_reason = reason
        application.reviewed_at = current_datetime()
        application.reviewer_id = admin_user.id
        self._user_repository.update_publisher_application(application)
        self._write_audit_log(admin_user.id, "publisher_application", application.id, "reject", "rejected", reason)
        self._notification_service.send_to_user(
            application.user_id,
            "发布者申请审核未通过",
            f"你的发布者申请审核未通过，原因：【{reason}】。",
            "publisher_application",
        )
        application = self._user_repository.find_publisher_application_by_id(application.id)
        return UserResult(True, "申请已驳回。", application=self._to_application_dto(application))

    def list_users(self, admin_user: Any, role_code: str | None = None) -> UserResult:
        if not PermissionChecker.is_admin(admin_user):
            return UserResult(False, PERMISSION_DENIED_MESSAGE)
        users = self._user_repository.list_by_role_code(role_code) if role_code else self._user_repository.list_all()
        return UserResult(True, "查询成功。", users=[self._to_user_dto(user) for user in users])

    def freeze_user(self, admin_user: Any, user_id: int) -> UserResult:
        if not PermissionChecker.is_admin(admin_user):
            return UserResult(False, PERMISSION_DENIED_MESSAGE)
        user = self._user_repository.find_by_id(user_id)
        if user is None:
            return UserResult(False, "用户不存在。")
        if user.id == admin_user.id:
            return UserResult(False, "不能冻结当前登录管理员。")
        user.status = "frozen"
        user.frozen_until = None
        user.updated_at = current_datetime()
        self._user_repository.update(user)
        self._write_audit_log(admin_user.id, "user", user.id, "freeze", "frozen", "管理员冻结账号")
        self._session.commit()
        user = self._user_repository.find_by_id(user.id)
        return UserResult(True, "用户已冻结。", user=self._to_user_dto(user))

    def unfreeze_user(self, admin_user: Any, user_id: int) -> UserResult:
        if not PermissionChecker.is_admin(admin_user):
            return UserResult(False, PERMISSION_DENIED_MESSAGE)
        user = self._user_repository.find_by_id(user_id)
        if user is None:
            return UserResult(False, "用户不存在。")
        user.status = "enabled"
        user.frozen_until = None
        user.updated_at = current_datetime()
        self._user_repository.update(user)
        self._write_audit_log(admin_user.id, "user", user.id, "unfreeze", "enabled", "管理员解冻账号")
        self._session.commit()
        user = self._user_repository.find_by_id(user.id)
        return UserResult(True, "用户已解冻。", user=self._to_user_dto(user))

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

    def _to_user_dto(self, user) -> UserDTO:
        return UserDTO(
            user_id=user.id,
            account=user.account,
            name=user.name,
            role_code=user.role.code if user.role else "",
            role_name=user.role.name if user.role else "",
            status=user.status,
            phone=user.phone,
            violation_count=user.violation_count,
            created_at=user.created_at,
        )

    def _to_application_dto(self, application: PublisherApplication) -> PublisherApplicationDTO:
        return PublisherApplicationDTO(
            application_id=application.id,
            user_id=application.user_id,
            account=application.user.account if application.user else "",
            user_name=application.user.name if application.user else "",
            organization_name=application.organization_name,
            responsible_person=application.responsible_person,
            contact_info=application.contact_info,
            application_note=application.proof_file,
            status=application.status,
            reject_reason=application.reject_reason,
            submitted_at=application.submitted_at,
            reviewed_at=application.reviewed_at,
        )
