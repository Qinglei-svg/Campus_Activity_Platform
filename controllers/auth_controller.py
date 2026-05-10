from __future__ import annotations

from sqlalchemy.orm import Session

from database.db import SessionLocal
from repositories.sqlite.sqlite_role_repository import SQLiteRoleRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from services.impl.auth_service_impl import AuthServiceImpl
from services.interfaces.auth_service import AuthenticatedUser, AuthResult


class AuthController:
    def __init__(self, session: Session | None = None) -> None:
        self._owns_session = session is None
        self._session = session or SessionLocal()
        user_repository = SQLiteUserRepository(self._session)
        role_repository = SQLiteRoleRepository(self._session)
        self._auth_service = AuthServiceImpl(
            session=self._session,
            user_repository=user_repository,
            role_repository=role_repository,
        )
        self._current_user: AuthenticatedUser | None = None

    def login(self, account: str, password: str) -> AuthResult:
        result = self._auth_service.login(account, password)
        if result.success:
            self._current_user = result.user
        return result

    def register(self, account: str, name: str, password: str, phone: str) -> AuthResult:
        return self._auth_service.register(account, name, password, phone)

    def logout(self) -> None:
        self._current_user = None

    def get_current_user(self) -> AuthenticatedUser | None:
        return self._current_user

    def close(self) -> None:
        if self._owns_session:
            self._session.close()
