from __future__ import annotations

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.activity_model import ActivityCategory
from repositories.interfaces.activity_category_repository import IActivityCategoryRepository
from repositories.interfaces.activity_repository import IActivityRepository
from services.interfaces.category_service import (
    ActivityCategoryManageDTO,
    CategoryResult,
    ICategoryService,
)
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


class CategoryServiceImpl(ICategoryService):
    def __init__(
        self,
        category_repository: IActivityCategoryRepository,
        activity_repository: IActivityRepository,
        session: Session | None = None,
    ) -> None:
        self._category_repository = category_repository
        self._activity_repository = activity_repository
        self._session = session

    def list_categories(self, admin_user: Any) -> CategoryResult:
        if not PermissionChecker.is_admin(admin_user):
            return CategoryResult(False, PERMISSION_DENIED_MESSAGE)

        categories = self._category_repository.list_all()
        return CategoryResult(
            True,
            "查询成功。",
            categories=[self._to_dto(category) for category in categories],
        )

    def create_category(self, admin_user: Any, name: str, description: str = "") -> CategoryResult:
        if not PermissionChecker.is_admin(admin_user):
            return CategoryResult(False, PERMISSION_DENIED_MESSAGE)

        cleaned_name = self._clean_name(name)
        if not cleaned_name:
            return CategoryResult(False, "分类名称不能为空。")
        if self._category_repository.find_by_name(cleaned_name) is not None:
            return CategoryResult(False, "分类名称不能重复。")

        category = ActivityCategory(
            name=cleaned_name,
            description=str(description or "").strip(),
            enabled=True,
        )
        try:
            self._category_repository.save(category)
            self._commit()
        except IntegrityError:
            self._rollback()
            return CategoryResult(False, "分类名称不能重复。")

        return CategoryResult(True, "分类创建成功。", category=self._to_dto(category))

    def update_category(
        self,
        admin_user: Any,
        category_id: int,
        name: str,
        description: str = "",
    ) -> CategoryResult:
        if not PermissionChecker.is_admin(admin_user):
            return CategoryResult(False, PERMISSION_DENIED_MESSAGE)

        category = self._category_repository.find_by_id(category_id)
        if category is None:
            return CategoryResult(False, "分类不存在。")

        cleaned_name = self._clean_name(name)
        if not cleaned_name:
            return CategoryResult(False, "分类名称不能为空。")
        existing = self._category_repository.find_by_name(cleaned_name)
        if existing is not None and existing.id != category.id:
            return CategoryResult(False, "分类名称不能重复。")

        category.name = cleaned_name
        category.description = str(description or "").strip()
        try:
            self._category_repository.update(category)
            self._commit()
        except IntegrityError:
            self._rollback()
            return CategoryResult(False, "分类名称不能重复。")

        return CategoryResult(True, "分类保存成功。", category=self._to_dto(category))

    def enable_category(self, admin_user: Any, category_id: int) -> CategoryResult:
        return self._set_category_enabled(admin_user, category_id, enabled=True)

    def disable_category(self, admin_user: Any, category_id: int) -> CategoryResult:
        return self._set_category_enabled(admin_user, category_id, enabled=False)

    def _set_category_enabled(self, admin_user: Any, category_id: int, enabled: bool) -> CategoryResult:
        if not PermissionChecker.is_admin(admin_user):
            return CategoryResult(False, PERMISSION_DENIED_MESSAGE)

        category = self._category_repository.find_by_id(category_id)
        if category is None:
            return CategoryResult(False, "分类不存在。")

        category.enabled = enabled
        self._category_repository.update(category)
        self._commit()
        message = "分类已启用。" if enabled else "分类已禁用。"
        return CategoryResult(True, message, category=self._to_dto(category))

    def _to_dto(self, category: ActivityCategory) -> ActivityCategoryManageDTO:
        return ActivityCategoryManageDTO(
            category_id=category.id,
            name=category.name,
            description=category.description,
            enabled=category.enabled,
            created_at=category.created_at,
            activity_count=self._activity_repository.count_by_category(category.id),
        )

    def _clean_name(self, name: str) -> str:
        return str(name or "").strip()

    def _commit(self) -> None:
        if self._session is not None:
            self._session.commit()

    def _rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()
