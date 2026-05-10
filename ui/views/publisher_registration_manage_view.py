from __future__ import annotations

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

from controllers.activity_controller import ActivityController
from controllers.export_controller import ExportController
from controllers.registration_controller import RegistrationController
from controllers.report_appeal_controller import ReportAppealController
from services.interfaces.activity_service import ActivityDTO
from ui.views.report_submit_dialog import ReportSubmitDialog
from ui.widgets.table_utils import configure_table, set_row_height, set_table_buttons, table_button, apply_table_column_resize


class PublisherRegistrationManageView(QWidget):
    def __init__(
        self,
        activity_controller: ActivityController,
        export_controller: ExportController,
        registration_controller: RegistrationController,
        report_appeal_controller: ReportAppealController,
    ) -> None:
        super().__init__()
        self._activity_controller = activity_controller
        self._export_controller = export_controller
        self._registration_controller = registration_controller
        self._report_appeal_controller = report_appeal_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("报名管理")
        title.setObjectName("pageTitle")

        toolbar = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_button)
        toolbar.addStretch(1)

        self._empty_label = QLabel("暂无可导出的活动")
        self._empty_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(["活动标题", "分类", "活动时间", "地点", "容量", "状态", "导出", "举报"])
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
        result = self._activity_controller.list_my_activities()
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render_activities(result.activities or [])

    def _render_activities(self, activities: list[ActivityDTO]) -> None:
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
                activity_time,
                activity.location,
                str(activity.capacity),
                activity.status,
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            export_button = table_button(
                "导出 Excel",
                lambda activity_id=activity.activity_id: self._export_activity(activity_id),
            )

            report_button = table_button(
                "举报参与者",
                lambda activity_id=activity.activity_id: self._open_participant_report(activity_id),
            )
            set_table_buttons(self._table, row, 6, export_button)
            set_table_buttons(self._table, row, 7, report_button)

        apply_table_column_resize(self._table, tail_action_columns=2)

    def _export_activity(self, activity_id: int) -> None:
        result = self._export_controller.export_activity_registration_excel(activity_id)
        if not result.success:
            QMessageBox.warning(self, "导出失败", result.message)
            return
        QMessageBox.information(self, "导出成功", f"Excel 文件已保存到：\n{result.file_path}")

    def _open_participant_report(self, activity_id: int) -> None:
        result = self._registration_controller.list_activity_registrations(activity_id)
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return

        registrations = [
            registration
            for registration in result.registrations or []
            if registration.status in {"registered", "approved", "checked_in", "waiting"}
        ]
        if not registrations:
            QMessageBox.information(self, "暂无参与者", "该活动暂无可举报的参与者。")
            return

        labels = {
            f"{registration.user_name}（{registration.user_account}）": registration.user_id
            for registration in registrations
        }
        selected, ok = QInputDialog.getItem(
            self,
            "举报参与者",
            "请选择参与者：",
            list(labels.keys()),
            0,
            False,
        )
        if not ok or not selected:
            return

        participant_id = labels[selected]
        dialog = ReportSubmitDialog(
            "举报参与者",
            f"举报参与者：{selected}",
            lambda reason: self._report_appeal_controller.submit_participant_report(participant_id, reason),
        )
        dialog.exec()
