from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.user_controller import UserController
from services.interfaces.user_service import UserDTO
from ui.widgets.table_utils import (
    apply_table_column_resize,
    configure_table,
    set_row_height,
    set_table_buttons,
    table_button,
)


class AdminUserManageView(QWidget):
    def __init__(self, user_controller: UserController) -> None:
        super().__init__()
        self._user_controller = user_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("用户管理")
        title.setObjectName("pageTitle")

        self._role_filter = QComboBox()
        self._role_filter.addItem("全部角色", None)
        self._role_filter.addItem("系统管理员", "admin")
        self._role_filter.addItem("活动发布者", "publisher")
        self._role_filter.addItem("活动参与者", "participant")
        self._role_filter.currentIndexChanged.connect(self.refresh)

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)

        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(["账号", "姓名", "角色", "状态", "手机号", "违规次数", "注册时间", "操作"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addWidget(self._role_filter)
        layout.addWidget(refresh_button)
        layout.addWidget(self._table, 1)
        self.refresh()

    def refresh(self) -> None:
        result = self._user_controller.list_users(self._role_filter.currentData())
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render(result.users or [])

    def _render(self, users: list[UserDTO]) -> None:
        self._table.setRowCount(len(users))
        for row, user in enumerate(users):
            set_row_height(self._table, row)
            values = [
                user.account,
                user.name,
                user.role_name,
                self._status_text(user.status),
                user.phone,
                str(user.violation_count),
                user.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            button = table_button(
                "解冻" if user.status == "frozen" else "冻结",
                lambda item=user: self._toggle_user_status(item),
                danger=user.status != "frozen",
            )
            set_table_buttons(self._table, row, 7, button)
        apply_table_column_resize(self._table)

    def _toggle_user_status(self, user: UserDTO) -> None:
        if user.status == "frozen":
            result = self._user_controller.unfreeze_user(user.user_id)
        else:
            result = self._user_controller.freeze_user(user.user_id)
        if not result.success:
            QMessageBox.warning(self, "操作失败", result.message)
            return
        QMessageBox.information(self, "操作成功", result.message)
        self.refresh()

    def _status_text(self, status: str) -> str:
        return {"enabled": "正常", "frozen": "已冻结"}.get(status, status)
