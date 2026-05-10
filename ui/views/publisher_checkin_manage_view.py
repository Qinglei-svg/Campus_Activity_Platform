from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.activity_controller import ActivityController
from controllers.checkin_controller import CheckinController
from services.interfaces.activity_service import ActivityDTO
from services.interfaces.checkin_service import CheckinRecordDTO
from ui.widgets.table_utils import configure_table, set_row_height, set_table_buttons, table_button, apply_table_column_resize


class PublisherCheckinManageView(QWidget):
    def __init__(self, activity_controller: ActivityController, checkin_controller: CheckinController) -> None:
        super().__init__()
        self._activity_controller = activity_controller
        self._checkin_controller = checkin_controller
        self._activities: list[ActivityDTO] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("签到管理")
        title.setObjectName("pageTitle")

        toolbar = QHBoxLayout()
        self._activity_combo = QComboBox()
        self._method_combo = QComboBox()
        self._method_combo.addItem("口令签到", "password")
        self._method_combo.addItem("二维码签到", "qrcode")
        self._code_input = QLineEdit()
        self._code_input.setPlaceholderText("请输入签到口令")

        enable_button = QPushButton("开启签到")
        enable_button.setObjectName("primaryButton")
        enable_button.clicked.connect(self._enable_checkin)

        refresh_button = QPushButton("刷新记录")
        refresh_button.clicked.connect(self.refresh_records)

        toolbar.addWidget(self._activity_combo, 2)
        toolbar.addWidget(self._method_combo)
        toolbar.addWidget(self._code_input, 1)
        toolbar.addWidget(enable_button)
        toolbar.addWidget(refresh_button)

        self._qr_label = QLabel("二维码将在开启二维码签到后显示")
        self._qr_label.setObjectName("placeholderHint")
        self._qr_label.setFixedHeight(170)

        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(["账号", "姓名", "报名状态", "签到状态", "签到方式", "签到时间", "修正原因", "操作"])
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addLayout(toolbar)
        layout.addWidget(self._qr_label)
        layout.addWidget(self._table, 1)

        self._load_activities()
        self._activity_combo.currentIndexChanged.connect(self.refresh_records)
        self.refresh_records()

    def _load_activities(self) -> None:
        result = self._activity_controller.list_my_activities()
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._activities = result.activities or []
        self._activity_combo.clear()
        for activity in self._activities:
            self._activity_combo.addItem(f"{activity.title}（{activity.status}）", activity.activity_id)

    def _enable_checkin(self) -> None:
        activity_id = self._activity_combo.currentData()
        if activity_id is None:
            QMessageBox.warning(self, "操作失败", "请先选择活动。")
            return
        result = self._checkin_controller.enable_checkin(
            activity_id,
            self._method_combo.currentData(),
            self._code_input.text(),
        )
        if not result.success:
            QMessageBox.warning(self, "操作失败", result.message)
            return
        QMessageBox.information(self, "操作成功", result.message)
        if result.qr_code_path is not None:
            self._show_qr_code(result.qr_code_path)
        self.refresh_records()

    def refresh_records(self) -> None:
        activity_id = self._activity_combo.currentData()
        if activity_id is None:
            self._table.setRowCount(0)
            return
        result = self._checkin_controller.list_activity_checkins(activity_id)
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render_checkins(result.checkins or [])

    def _render_checkins(self, checkins: list[CheckinRecordDTO]) -> None:
        self._table.setRowCount(len(checkins))
        for row, item in enumerate(checkins):
            set_row_height(self._table, row)
            values = [
                item.user_account,
                item.user_name,
                self._registration_status_text(item.registration_status),
                self._checkin_status_text(item.status),
                item.checkin_method,
                "" if item.checkin_time is None else item.checkin_time.strftime("%Y-%m-%d %H:%M"),
                item.correction_reason,
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            correct_button = table_button(
                "修正签到",
                lambda registration_id=item.registration_id: self._correct_checkin(registration_id),
                enabled=item.registration_id is not None,
            )
            set_table_buttons(self._table, row, 7, correct_button)
        apply_table_column_resize(self._table)

    def _correct_checkin(self, registration_id: int | None) -> None:
        if registration_id is None:
            return
        reason, ok = QInputDialog.getText(self, "修正签到", "请输入修正原因：")
        if not ok:
            return
        result = self._checkin_controller.correct_checkin(registration_id, "checked_in", reason)
        if not result.success:
            QMessageBox.warning(self, "修正失败", result.message)
            return
        QMessageBox.information(self, "修正成功", result.message)
        self.refresh_records()

    def _show_qr_code(self, path: Path) -> None:
        pixmap = QPixmap(str(path))
        self._qr_label.setPixmap(pixmap.scaled(160, 160))

    def _registration_status_text(self, status: str) -> str:
        return {"registered": "已报名", "waiting": "候补中", "canceled": "已取消"}.get(status, status)

    def _checkin_status_text(self, status: str) -> str:
        return {"checked_in": "已签到", "not_checked_in": "未签到", "absent": "未签到", "corrected": "补签"}.get(status, status)
