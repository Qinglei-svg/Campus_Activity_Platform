from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.audit_log_controller import AuditLogController
from services.interfaces.audit_log_service import AuditLogDTO
from ui.widgets.table_utils import configure_table, set_row_height


class AdminAuditLogView(QWidget):
    def __init__(self, audit_log_controller: AuditLogController) -> None:
        super().__init__()
        self._audit_log_controller = audit_log_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("操作日志")
        title.setObjectName("pageTitle")

        toolbar = QHBoxLayout()
        self._action_filter = QComboBox()
        self._action_filter.addItem("全部操作", None)
        self._load_action_options()
        self._action_filter.currentIndexChanged.connect(self.refresh)

        self._operator_filter = QLineEdit()
        self._operator_filter.setPlaceholderText("按操作人账号或姓名筛选")

        search_button = QPushButton("筛选")
        search_button.setObjectName("primaryButton")
        search_button.clicked.connect(self.refresh)

        reset_button = QPushButton("重置")
        reset_button.clicked.connect(self._reset_filters)

        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh)

        toolbar.addWidget(self._action_filter)
        toolbar.addWidget(self._operator_filter, 1)
        toolbar.addWidget(search_button)
        toolbar.addWidget(reset_button)
        toolbar.addWidget(refresh_button)

        self._empty_label = QLabel("暂无操作日志")
        self._empty_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 9)
        self._table.setHorizontalHeaderLabels(
            ["操作时间", "操作人", "角色", "操作类型", "操作结果", "目标类型", "目标ID", "原因说明", "日志ID"]
        )
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
        result = self._audit_log_controller.list_logs(
            action=self._action_filter.currentData(),
            operator_keyword=self._operator_filter.text(),
        )
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render_logs(result.logs or [])

    def _load_action_options(self) -> None:
        result = self._audit_log_controller.list_action_options()
        if not result.success:
            return
        for action, label in result.actions or []:
            self._action_filter.addItem(label, action)

    def _render_logs(self, logs: list[AuditLogDTO]) -> None:
        self._empty_label.setVisible(not logs)
        self._table.setVisible(bool(logs))
        self._table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            set_row_height(self._table, row)
            values = [
                log.operated_at.strftime("%Y-%m-%d %H:%M:%S"),
                f"{log.operator_name}（{log.operator_account}）",
                log.operator_role_name,
                log.action_name,
                log.result,
                self._target_type_text(log.target_type),
                str(log.target_id),
                log.reason,
                str(log.log_id),
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))
        self._table.resizeColumnsToContents()

    def _reset_filters(self) -> None:
        self._action_filter.setCurrentIndex(0)
        self._operator_filter.clear()
        self.refresh()

    def _target_type_text(self, target_type: str) -> str:
        return {
            "activity": "活动",
            "user": "用户",
            "checkin_record": "签到记录",
            "review": "评价",
            "report_appeal": "举报申诉",
            "publisher_application": "发布者申请",
        }.get(target_type, target_type)
