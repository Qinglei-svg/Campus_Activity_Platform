from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.registration_controller import RegistrationController
from services.interfaces.registration_service import RegistrationDTO
from ui.widgets.table_utils import configure_table, set_row_height, set_table_buttons, table_button


class MyRegistrationView(QWidget):
    def __init__(self, registration_controller: RegistrationController) -> None:
        super().__init__()
        self._registration_controller = registration_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("我的报名")
        title.setObjectName("pageTitle")

        toolbar = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_button)
        toolbar.addStretch(1)

        self._empty_label = QLabel("暂无报名记录")
        self._empty_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(
            ["活动标题", "分类", "活动时间", "地点", "报名状态", "候补顺序", "报名时间", "操作"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addLayout(toolbar)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table, 1)

        self.refresh()

    def refresh(self) -> None:
        result = self._registration_controller.list_my_registrations()
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render_registrations(result.registrations or [])

    def _render_registrations(self, registrations: list[RegistrationDTO]) -> None:
        self._table.setRowCount(len(registrations))
        self._empty_label.setVisible(len(registrations) == 0)
        self._table.setVisible(len(registrations) > 0)

        for row, registration in enumerate(registrations):
            set_row_height(self._table, row)
            activity_time = (
                f"{registration.start_time.strftime('%Y-%m-%d %H:%M')} 至 "
                f"{registration.end_time.strftime('%Y-%m-%d %H:%M')}"
            )
            values = [
                registration.activity_title,
                registration.category_name,
                activity_time,
                registration.location,
                self._status_text(registration),
                "" if registration.waiting_order is None else str(registration.waiting_order),
                registration.registered_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            cancel_button = table_button(
                "取消报名",
                lambda registration_id=registration.registration_id: self._cancel_registration(registration_id),
                enabled=registration.status in {"registered", "waiting", "approved"},
            )
            set_table_buttons(self._table, row, 7, cancel_button)

        self._table.resizeColumnsToContents()

    def _cancel_registration(self, registration_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "确认取消报名",
            "确定要取消该报名吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        result = self._registration_controller.cancel_registration(registration_id)
        if not result.success:
            QMessageBox.warning(self, "取消失败", result.message)
            return
        QMessageBox.information(self, "取消成功", result.message)
        self.refresh()

    def _status_text(self, registration: RegistrationDTO) -> str:
        status_map = {
            "registered": "已报名",
            "waiting": "候补中",
            "canceled": "已取消",
            "approved": "已报名",
        }
        return status_map.get(registration.status, registration.status)
