from __future__ import annotations

from PySide6.QtWidgets import QInputDialog, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.user_controller import UserController
from services.interfaces.user_service import PublisherApplicationDTO
from ui.widgets.table_utils import configure_table, set_row_height, set_table_buttons, table_button


class AdminPublisherAuditView(QWidget):
    def __init__(self, user_controller: UserController) -> None:
        super().__init__()
        self._user_controller = user_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("发布者审核")
        title.setObjectName("pageTitle")

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)

        self._table = QTableWidget(0, 10)
        self._table.setHorizontalHeaderLabels(
            ["账号", "姓名", "组织名称", "负责人", "联系方式", "申请说明", "状态", "驳回原因", "提交时间", "操作"]
        )
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addWidget(refresh_button)
        layout.addWidget(self._table, 1)
        self.refresh()

    def refresh(self) -> None:
        result = self._user_controller.list_publisher_applications()
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render(result.applications or [])

    def _render(self, applications: list[PublisherApplicationDTO]) -> None:
        self._table.setRowCount(len(applications))
        for row, application in enumerate(applications):
            set_row_height(self._table, row)
            values = [
                application.account,
                application.user_name,
                application.organization_name,
                application.responsible_person,
                application.contact_info,
                application.application_note,
                self._status_text(application.status),
                application.reject_reason,
                application.submitted_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            approve_button = table_button(
                "通过",
                lambda application_id=application.application_id: self._approve(application_id),
                enabled=application.status == "pending",
            )
            reject_button = table_button(
                "驳回",
                lambda application_id=application.application_id: self._reject(application_id),
                danger=True,
                enabled=application.status == "pending",
            )
            set_table_buttons(self._table, row, 9, approve_button, reject_button)
        self._table.resizeColumnsToContents()

    def _approve(self, application_id: int) -> None:
        result = self._user_controller.approve_publisher_application(application_id)
        if not result.success:
            QMessageBox.warning(self, "审核失败", result.message)
            return
        QMessageBox.information(self, "审核成功", result.message)
        self.refresh()

    def _reject(self, application_id: int) -> None:
        reason, ok = QInputDialog.getText(self, "驳回申请", "请输入驳回原因：")
        if not ok:
            return
        result = self._user_controller.reject_publisher_application(application_id, reason)
        if not result.success:
            QMessageBox.warning(self, "审核失败", result.message)
            return
        QMessageBox.information(self, "审核成功", result.message)
        self.refresh()

    def _status_text(self, status: str) -> str:
        return {"pending": "待审核", "approved": "已通过", "rejected": "已驳回"}.get(status, status)
