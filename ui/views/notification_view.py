from __future__ import annotations

from PySide6.QtCore import Qt
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

from controllers.notification_controller import NotificationController
from services.interfaces.auth_service import AuthenticatedUser
from services.interfaces.notification_service import NotificationDTO
from ui.widgets.table_utils import apply_table_column_resize, configure_table, set_row_height


class NotificationView(QWidget):
    def __init__(self, user: AuthenticatedUser, notification_controller: NotificationController) -> None:
        super().__init__()
        self._user = user
        self._notification_controller = notification_controller
        self._notification_ids: list[int] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("通知中心")
        title.setObjectName("pageTitle")

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh)

        mark_read_button = QPushButton("标记已读")
        mark_read_button.clicked.connect(self._mark_selected_as_read)

        delete_button = QPushButton("删除")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self._delete_selected)

        toolbar.addWidget(refresh_button)
        toolbar.addWidget(mark_read_button)
        toolbar.addWidget(delete_button)
        toolbar.addStretch(1)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["标题", "内容", "时间", "状态"])
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addLayout(toolbar)
        layout.addWidget(self._table, 1)

        self.refresh()

    def refresh(self) -> None:
        result = self._notification_controller.list_user_notifications(self._user.id)
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render_notifications(result.notifications or [])

    def _render_notifications(self, notifications: list[NotificationDTO]) -> None:
        self._notification_ids = [notification.id for notification in notifications]
        self._table.setRowCount(len(notifications))

        for row, notification in enumerate(notifications):
            set_row_height(self._table, row)
            status_text = "已读" if notification.is_read else "未读"
            created_at_text = notification.created_at.strftime("%Y-%m-%d %H:%M")
            items = [
                QTableWidgetItem(notification.title),
                QTableWidgetItem(notification.content),
                QTableWidgetItem(created_at_text),
                QTableWidgetItem(status_text),
            ]
            for item in items:
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

        apply_table_column_resize(self._table)

    def _get_selected_notification_id(self) -> int | None:
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择一条通知。")
            return None
        row = selected_rows[0].row()
        return self._notification_ids[row]

    def _mark_selected_as_read(self) -> None:
        notification_id = self._get_selected_notification_id()
        if notification_id is None:
            return

        result = self._notification_controller.mark_as_read(notification_id)
        if not result.success:
            QMessageBox.warning(self, "操作失败", result.message)
            return
        self.refresh()

    def _delete_selected(self) -> None:
        notification_id = self._get_selected_notification_id()
        if notification_id is None:
            return

        result = self._notification_controller.delete_notification(notification_id)
        if not result.success:
            QMessageBox.warning(self, "操作失败", result.message)
            return
        self.refresh()
