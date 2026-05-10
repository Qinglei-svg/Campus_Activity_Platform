from __future__ import annotations

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QCalendarWidget,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.activity_controller import ActivityController
from controllers.statistics_controller import StatisticsController
from services.interfaces.activity_service import ActivityDTO
from services.interfaces.statistics_service import ActivityCalendarEventDTO, PublisherStatisticsDTO
from ui.widgets.table_utils import configure_table, set_row_height, set_table_buttons, table_button


class PublisherActivityManageView(QWidget):
    detail_requested = Signal(int)
    edit_requested = Signal(int)

    STATUS_OPTIONS = [
        ("全部", None),
        ("draft 草稿", "draft"),
        ("pending_review 待审核", "pending_review"),
        ("rejected 已驳回", "rejected"),
        ("online 已上线", "online"),
        ("cancelled 已取消", "cancelled"),
        ("archived 已归档", "archived"),
    ]

    def __init__(
        self,
        activity_controller: ActivityController,
        statistics_controller: StatisticsController | None = None,
    ) -> None:
        super().__init__()
        self._activity_controller = activity_controller
        self._statistics_controller = statistics_controller
        self._activity_ids: list[int] = []
        self._calendar_events: list[ActivityCalendarEventDTO] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("我的活动")
        title.setObjectName("pageTitle")

        toolbar = QHBoxLayout()
        self._status_combo = QComboBox()
        for label, status in self.STATUS_OPTIONS:
            self._status_combo.addItem(label, status)

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)

        self._statistics_layout = QGridLayout()
        self._statistics_layout.setSpacing(10)

        self._calendar = QCalendarWidget()
        self._calendar.selectionChanged.connect(self._render_selected_date_events)
        self._calendar_label = QLabel("请选择日期查看活动安排")
        self._calendar_label.setObjectName("placeholderHint")

        toolbar.addWidget(self._status_combo)
        toolbar.addWidget(refresh_button)
        toolbar.addStretch(1)

        self._empty_label = QLabel("暂无活动")
        self._empty_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 10)
        self._table.setHorizontalHeaderLabels(
            ["活动标题", "分类", "活动时间", "地点", "容量", "当前状态", "驳回原因", "更新时间", "查看详情", "操作"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addLayout(self._statistics_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table, 1)
        layout.addWidget(QLabel("活动日历"))
        layout.addWidget(self._calendar)
        layout.addWidget(self._calendar_label)

        self._status_combo.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self._load_statistics()
        self._load_calendar_events()
        result = self._activity_controller.list_my_activities(status=self._status_combo.currentData())
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
                activity_time,
                activity.location,
                str(activity.capacity),
                activity.status,
                activity.reject_reason,
                activity.updated_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            detail_button = table_button(
                "查看详情",
                lambda activity_id=activity.activity_id: self.detail_requested.emit(activity_id),
            )

            edit_button = table_button(
                "编辑草稿",
                lambda activity_id=activity.activity_id: self.edit_requested.emit(activity_id),
                enabled=activity.status in {"draft", "rejected"},
            )

            submit_button = table_button(
                "提交审核",
                lambda activity_id=activity.activity_id: self._submit_activity(activity_id),
                enabled=activity.status in {"draft", "rejected"},
            )
            set_table_buttons(self._table, row, 8, detail_button)
            set_table_buttons(self._table, row, 9, edit_button, submit_button)

        self._table.resizeColumnsToContents()

    def _load_statistics(self) -> None:
        if self._statistics_controller is None:
            return
        result = self._statistics_controller.get_publisher_statistics()
        if not result.success or result.publisher_statistics is None:
            return
        self._render_statistics(result.publisher_statistics)

    def _render_statistics(self, statistics: PublisherStatisticsDTO) -> None:
        while self._statistics_layout.count():
            item = self._statistics_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        cards = [
            ("我发布的活动数", statistics.activity_count),
            ("总报名数", statistics.total_registrations),
            ("总签到数", statistics.total_checkins),
            ("平均签到率", f"{statistics.average_checkin_rate * 100:.1f}%"),
            ("平均评分", f"{statistics.average_score:.1f}"),
        ]
        for index, (label, value) in enumerate(cards):
            card = QLabel(f"{label}\n{value}")
            card.setObjectName("statCard")
            self._statistics_layout.addWidget(card, index // 3, index % 3)

    def _load_calendar_events(self) -> None:
        if self._statistics_controller is None:
            return
        result = self._statistics_controller.list_publisher_calendar_events()
        if result.success:
            self._calendar_events = result.calendar_events or []
            self._render_selected_date_events()

    def _render_selected_date_events(self) -> None:
        selected = self._calendar.selectedDate()
        matched = [
            event
            for event in self._calendar_events
            if QDate(event.start_time.year, event.start_time.month, event.start_time.day) == selected
        ]
        if not matched:
            self._calendar_label.setText("所选日期暂无活动安排")
            return
        lines = [
            f"{event.start_time.strftime('%H:%M')} {event.title}（{event.status}，{event.location}）"
            for event in matched
        ]
        self._calendar_label.setText("\n".join(lines))

    def _submit_activity(self, activity_id: int) -> None:
        result = self._activity_controller.submit_activity(activity_id)
        if not result.success:
            QMessageBox.warning(self, "提交失败", result.message)
            return
        QMessageBox.information(self, "提交成功", "活动已提交审核")
        self.refresh()
