from __future__ import annotations

from uuid import uuid4

from controllers.audit_log_controller import AuditLogController
from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from database.db import SessionLocal, initialize_database


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


def _register_participant():
    account = f"audit_log_user_{uuid4().hex[:8]}"
    password = "test123456"
    controller = AuthController()
    try:
        result = controller.register(account, f"日志测试用户{uuid4().hex[:4]}", password, "13800000000")
        assert result.success is True
        assert result.user is not None
        return result.user
    finally:
        controller.close()


def test_admin_can_list_audit_log_action_options() -> None:
    admin = _login("admin", "admin123")
    with SessionLocal() as session:
        result = AuditLogController(session=session, current_user=admin).list_action_options()

        assert result.success is True
        actions = dict(result.actions or [])
        assert actions["approve"] == "活动审核通过"
        assert actions["reject"] == "活动审核驳回"
        assert actions["freeze"] == "冻结用户"
        assert actions["unfreeze"] == "解冻用户"
        assert actions["correct_checkin"] == "手动修正签到"
        assert actions["delete_review"] == "删除评价"
        assert actions["punish"] == "举报处罚"
        assert actions["ignore"] == "举报不做处理"


def test_non_admin_cannot_list_audit_logs() -> None:
    participant = _login("student", "student123")
    with SessionLocal() as session:
        result = AuditLogController(session=session, current_user=participant).list_logs()

        assert result.success is False
        assert result.message == "当前角色无权执行该操作"


def test_admin_can_filter_audit_logs_by_action_and_operator() -> None:
    admin = _login("admin", "admin123")
    target_user = _register_participant()
    with SessionLocal() as session:
        freeze_result = UserController(session=session, current_user=admin).freeze_user(target_user.id)
        assert freeze_result.success is True

        controller = AuditLogController(session=session, current_user=admin)
        by_action = controller.list_logs(action="freeze")
        by_operator = controller.list_logs(operator_keyword="admin")
        by_both = controller.list_logs(action="freeze", operator_keyword=admin.name)

        assert by_action.success is True
        assert any(log.target_id == target_user.id and log.action == "freeze" for log in by_action.logs or [])
        assert by_operator.success is True
        assert all("admin" in log.operator_account or "admin" in log.operator_name for log in by_operator.logs or [])
        assert by_both.success is True
        assert any(log.target_id == target_user.id and log.action == "freeze" for log in by_both.logs or [])
