from __future__ import annotations

from abc import ABC, abstractmethod

from models.role_model import Role


class IRoleRepository(ABC):
    @abstractmethod
    def find_by_code(self, code: str) -> Role | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, role_id: int) -> Role | None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Role]:
        raise NotImplementedError
