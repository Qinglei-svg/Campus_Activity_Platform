from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.report_appeal_controller import ReportAppealController
from services.interfaces.report_appeal_service import ReportAppealDTO
from ui.widgets.table_utils import configure_table, set_row_height


class ParticipantReportView(QWidget):
    def __init__(self, report_controller: ReportAppealController) -> None:
        super().__init__()
        self._report_controller = report_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("举报申诉")
        title.setObjectName("pageTitle")

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)

        self._empty_label = QLabel("暂无举报记录")
        self._empty_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(["举报对象", "原因", "状态", "处理结果", "处理人", "提交时间", "处理时间"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addWidget(refresh_button)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table, 1)
        self.refresh()

    def refresh(self) -> None:
        result = self._report_controller.list_my_reports()
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
                report.target_name,
                report.reason,
                self._status_text(report.status),
                report.result,
                report.handler_name,
                report.submitted_at.strftime("%Y-%m-%d %H:%M"),
                report.handled_at.strftime("%Y-%m-%d %H:%M") if report.handled_at else "",
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))
        self._table.resizeColumnsToContents()

    def _status_text(self, status: str) -> str:
        return {"pending": "待处理", "punished": "已处罚", "ignored": "不做处理"}.get(status, status)
