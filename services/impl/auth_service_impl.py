from __future__ import annotations

from sqlalchemy.orm import Session

from models.user_model import User
from repositories.interfaces.role_repository import IRoleRepository
from repositories.interfaces.user_repository import IUserRepository
from services.interfaces.auth_service import AuthenticatedUser, AuthResult, IAuthService
from utils.datetime_utils import current_datetime
from utils.password_utils import hash_password, verify_password


class AuthServiceImpl(IAuthService):
    def __init__(
        self,
        session: Session,
        user_repository: IUserRepository,
        role_repository: IRoleRepository,
    ) -> None:
        self._session = session
        self._user_repository = user_repository
        self._role_repository = role_repository

    def login(self, account: str, password: str) -> AuthResult:
        account = account.strip()
        if not account or not password:
            return AuthResult(False, "请输入账号和密码。")

        user = self._user_repository.find_by_account(account)
        if user is None:
            return AuthResult(False, "账号不存在。")

        if user.status == "frozen":
            if user.frozen_until is not None and user.frozen_until <= current_datetime():
                user.status = "enabled"
                user.frozen_until = None
                self._user_repository.update(user)
                self._session.commit()
            else:
                return AuthResult(False, "该账号已被冻结，无法登录。")

        if not verify_password(password, user.password_hash):
            return AuthResult(False, "密码错误。")

        return AuthResult(True, "登录成功。", self._to_authenticated_user(user))

    def register(self, account: str, name: str, password: str, phone: str) -> AuthResult:
        account = account.strip()
        name = name.strip()
        phone = phone.strip()

        if not account or not name or not password:
            return AuthResult(False, "账号、姓名和密码不能为空。")

        if self._user_repository.find_by_account(account) is not None:
            return AuthResult(False, "账号已存在。")

        participant_role = self._role_repository.find_by_code("participant")
        if participant_role is None:
            return AuthResult(False, "系统缺少默认参与者角色，请先初始化数据库。")

        user = User(
            role_id=participant_role.id,
            account=account,
            name=name,
            password_hash=hash_password(password),
            auth_status="approved",
            status="enabled",
            phone=phone,
            violation_count=0,
        )
        self._user_repository.save(user)
        self._session.commit()
        user.role = participant_role
        return AuthResult(True, "注册成功。", self._to_authenticated_user(user))

    def change_password(self, user_id: int, old_password: str, new_password: str) -> AuthResult:
        if not old_password or not new_password:
            return AuthResult(False, "旧密码和新密码不能为空。")

        user = self._user_repository.find_by_id(user_id)
        if user is None:
            return AuthResult(False, "用户不存在。")

        if not verify_password(old_password, user.password_hash):
            return AuthResult(False, "旧密码错误。")

        user.password_hash = hash_password(new_password)
        self._user_repository.update(user)
        self._session.commit()
        return AuthResult(True, "密码修改成功。", self._to_authenticated_user(user))

    def _to_authenticated_user(self, user: User) -> AuthenticatedUser:
        return AuthenticatedUser(
            id=user.id,
            account=user.account,
            name=user.name,
            phone=user.phone,
            role_id=user.role_id,
            role_code=user.role.code,
            role_name=user.role.name,
            status=user.status,
        )
