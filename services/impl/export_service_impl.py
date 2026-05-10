from __future__ import annotations

import re
from pathlib import Path

from openpyxl import Workbook

from config.paths import EXPORTS_DIR
from repositories.interfaces.activity_repository import IActivityRepository
from repositories.interfaces.checkin_repository import ICheckinRepository
from repositories.interfaces.registration_repository import IRegistrationRepository
from services.interfaces.export_service import ExportResult, IExportService
from utils.datetime_utils import current_datetime
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


REGISTRATION_STATUS_TEXT = {
    "registered": "已报名",
    "waiting": "候补中",
    "canceled": "已取消",
    "approved": "已报名",
    "checked_in": "已签到",
}

CHECKIN_STATUS_TEXT = {
    "checked_in": "已签到",
    "absent": "未签到",
    "corrected": "补签",
}


class ExportServiceImpl(IExportService):
    def __init__(
        self,
        activity_repository: IActivityRepository,
        registration_repository: IRegistrationRepository,
        checkin_repository: ICheckinRepository,
    ) -> None:
        self._activity_repository = activity_repository
        self._registration_repository = registration_repository
        self._checkin_repository = checkin_repository

    def export_activity_registration_excel(self, current_user, activity_id: int) -> ExportResult:
        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return ExportResult(False, "活动不存在。")

        if not self._can_export(current_user, activity):
            return ExportResult(False, PERMISSION_DENIED_MESSAGE)

        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = EXPORTS_DIR / self._build_file_name(activity.title, activity.id)

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "报名签到名单"
        headers = ["活动标题", "用户账号", "用户姓名", "报名状态", "报名时间", "候补顺序", "签到状态"]
        sheet.append(headers)

        registrations = self._registration_repository.list_by_activity(activity_id)
        for registration in registrations:
            checkin = self._checkin_repository.find_by_registration(registration.id)
            sheet.append(
                [
                    activity.title,
                    registration.user.account if registration.user else "",
                    registration.user.name if registration.user else "",
                    REGISTRATION_STATUS_TEXT.get(registration.status, registration.status),
                    registration.registered_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "" if registration.waiting_order is None else registration.waiting_order,
                    self._checkin_status_text(checkin.status if checkin is not None else None),
                ]
            )

        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = max(max_length + 2, 12)

        workbook.save(file_path)
        return ExportResult(True, "导出成功。", file_path=file_path)

    def _can_export(self, current_user, activity) -> bool:
        if PermissionChecker.is_admin(current_user):
            return True
        return PermissionChecker.is_publisher(current_user) and activity.publisher_id == current_user.id

    def _build_file_name(self, title: str, activity_id: int) -> str:
        safe_title = re.sub(r'[\\/:*?"<>|\\s]+', "_", title).strip("_") or "activity"
        timestamp = current_datetime().strftime("%Y%m%d%H%M%S")
        return f"{safe_title}_{activity_id}_报名签到名单_{timestamp}.xlsx"

    def _checkin_status_text(self, status: str | None) -> str:
        if status is None:
            return "未签到"
        return CHECKIN_STATUS_TEXT.get(status, status)
