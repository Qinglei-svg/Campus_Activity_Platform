from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.admin_controller import AdminController
from services.interfaces.activity_service import ActivityDTO
from ui.widgets.table_utils import apply_table_column_resize, configure_table, set_row_height, set_table_buttons, table_button


class AdminActivityAuditView(QWidget):
    detail_requested = Signal(int)

    def __init__(self, admin_controller: AdminController) -> None:
        super().__init__()
        self._admin_controller = admin_controller
        self._activity_ids: list[int] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("活动审核")
        title.setObjectName("pageTitle")

        toolbar = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_button)
        toolbar.addStretch(1)

        self._empty_label = QLabel("暂无待审核活动")
        self._empty_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 10)
        self._table.setHorizontalHeaderLabels(
            ["活动标题", "分类", "发布者", "活动时间", "地点", "容量", "状态", "查看详情", "审核通过", "审核驳回"]
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
        result = self._admin_controller.list_pending_activities()
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render_activities(result.activities or [])

    def _render_activities(self, activities: list[ActivityDTO]) -> None:
        self._activity_ids = [activity.activity_id for activity in activities]
        self._table.setRowCount(len(activities))
        self._empty_label.setVisible(len(activities) == 0)
        self._table.setVisible(len(activities) > 0)

        for row, activity in enumerate(activities):
            set_row_height(self._table, row)
            activity_time = (
                f"{activity.start_time.strftime('%Y-%m-%d %H:%M')} 至 "
                f"{activity.end_time.strftime('%Y-%m-%d %H:%M')}"
            )
            values = [
                activity.title,
                activity.category_name,
                activity.publisher_name,
                activity_time,
                activity.location,
                str(activity.capacity),
                activity.status,
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            detail_button = table_button(
                "查看详情",
                lambda activity_id=activity.activity_id: self.detail_requested.emit(activity_id),
            )

            approve_button = table_button(
                "审核通过",
                lambda activity_id=activity.activity_id: self._approve_activity(activity_id),
            )

            reject_button = table_button(
                "审核驳回",
                lambda activity_id=activity.activity_id: self._reject_activity(activity_id),
                danger=True,
            )
            set_table_buttons(self._table, row, 7, detail_button)
            set_table_buttons(self._table, row, 8, approve_button)
            set_table_buttons(self._table, row, 9, reject_button)

        apply_table_column_resize(self._table, tail_action_columns=3)

    def _approve_activity(self, activity_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "确认审核通过",
            "确定要审核通过该活动吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        result = self._admin_controller.approve_activity(activity_id)
        if not result.success:
            QMessageBox.warning(self, "操作失败", result.message)
            return
        QMessageBox.information(self, "操作成功", "活动已审核通过")
        self.refresh()

    def _reject_activity(self, activity_id: int) -> None:
        reason, ok = QInputDialog.getText(self, "审核驳回", "请输入驳回原因：")
        if not ok:
            return
        result = self._admin_controller.reject_activity(activity_id, reason)
        if not result.success:
            QMessageBox.warning(self, "操作失败", result.message)
            return
        QMessageBox.information(self, "操作成功", "活动已驳回")
        self.refresh()
