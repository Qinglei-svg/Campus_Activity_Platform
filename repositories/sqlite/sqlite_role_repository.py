from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.role_model import Role
from repositories.interfaces.role_repository import IRoleRepository


class SQLiteRoleRepository(IRoleRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_code(self, code: str) -> Role | None:
        return self._session.scalar(select(Role).where(Role.code == code))

    def find_by_id(self, role_id: int) -> Role | None:
        return self._session.get(Role, role_id)

    def list_all(self) -> list[Role]:
        return list(self._session.scalars(select(Role).order_by(Role.id)).all())
