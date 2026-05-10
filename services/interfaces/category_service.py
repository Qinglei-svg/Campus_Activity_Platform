from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ActivityCategoryManageDTO:
    category_id: int
    name: str
    description: str
    enabled: bool
    created_at: datetime
    activity_count: int


@dataclass(frozen=True)
class CategoryResult:
    success: bool
    message: str
    category: ActivityCategoryManageDTO | None = None
    categories: list[ActivityCategoryManageDTO] | None = None


class ICategoryService(ABC):
    @abstractmethod
    def list_categories(self, admin_user: Any) -> CategoryResult:
        raise NotImplementedError

    @abstractmethod
    def create_category(self, admin_user: Any, name: str, description: str = "") -> CategoryResult:
        raise NotImplementedError

    @abstractmethod
    def update_category(
        self,
        admin_user: Any,
        category_id: int,
        name: str,
        description: str = "",
    ) -> CategoryResult:
        raise NotImplementedError

    @abstractmethod
    def enable_category(self, admin_user: Any, category_id: int) -> CategoryResult:
        raise NotImplementedError

    @abstractmethod
    def disable_category(self, admin_user: Any, category_id: int) -> CategoryResult:
        raise NotImplementedError
