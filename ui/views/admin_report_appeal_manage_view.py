from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
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

from controllers.report_appeal_controller import ReportAppealController
from services.interfaces.report_appeal_service import ReportAppealDTO
from ui.widgets.table_utils import apply_table_column_resize, configure_table, set_row_height, set_table_buttons, table_button


class AdminReportAppealManageView(QWidget):
    STATUS_OPTIONS = [
        ("全部", None),
        ("待处理", "pending"),
        ("已处罚", "punished"),
        ("不做处理", "ignored"),
    ]

    def __init__(self, report_controller: ReportAppealController) -> None:
        super().__init__()
        self._report_controller = report_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("举报申诉处理")
        title.setObjectName("pageTitle")

        toolbar = QHBoxLayout()
        self._status_combo = QComboBox()
        for label, status in self.STATUS_OPTIONS:
            self._status_combo.addItem(label, status)
        self._status_combo.currentIndexChanged.connect(self.refresh)

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(self._status_combo)
        toolbar.addWidget(refresh_button)
        toolbar.addStretch(1)

        self._empty_label = QLabel("暂无举报申诉记录")
        self._empty_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 10)
        self._table.setHorizontalHeaderLabels(
            ["提交人", "角色", "举报对象", "原因", "状态", "处理结果", "提交时间", "处理时间", "处罚", "不处理"]
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
        result = self._report_controller.list_reports(status=self._status_combo.currentData())
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render(result.reports or [])

    def _render(self, reports: list[ReportAppealDTO]) -> None:
        self._empty_label.setVisible(not reports)
        self._table.setVisible(bool(reports))
        self._table.setRowCount(len(reports))
        for row, report in enumerate(reports):
            set_row_height(self._table, row)
            values = [
                f"{report.submitter_name}（{report.submitter_account}）",
                report.submitter_role_name,
                report.target_name,
                report.reason,
                self._status_text(report.status),
                report.result,
                report.submitted_at.strftime("%Y-%m-%d %H:%M"),
                report.handled_at.strftime("%Y-%m-%d %H:%M") if report.handled_at else "",
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            punish_button = table_button(
                "处罚1天",
                lambda report_id=report.report_id: self._punish(report_id),
                danger=True,
                enabled=report.status == "pending",
            )

            ignore_button = table_button(
                "不做处理",
                lambda report_id=report.report_id: self._ignore(report_id),
                enabled=report.status == "pending",
            )
            set_table_buttons(self._table, row, 8, punish_button)
            set_table_buttons(self._table, row, 9, ignore_button)

        apply_table_column_resize(self._table, tail_action_columns=2)

    def _punish(self, report_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "确认处罚",
            "确认对举报对象执行 1 天内禁止登录的处罚吗？",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        result = self._report_controller.punish_report(report_id)
        if not result.success:
            QMessageBox.warning(self, "处罚失败", result.message)
            return
        QMessageBox.information(self, "处罚成功", result.message)
        self.refresh()

    def _ignore(self, report_id: int) -> None:
        reason, ok = QInputDialog.getMultiLineText(
            self,
            "不做处理",
            "处理说明：",
            "管理员核查后决定不做处理。",
        )
        if not ok:
            return
        result = self._report_controller.ignore_report(report_id, reason)
        if not result.success:
            QMessageBox.warning(self, "处理失败", result.message)
            return
        QMessageBox.information(self, "处理成功", result.message)
        self.refresh()

    def _status_text(self, status: str) -> str:
        return {"pending": "待处理", "punished": "已处罚", "ignored": "不做处理"}.get(status, status)
