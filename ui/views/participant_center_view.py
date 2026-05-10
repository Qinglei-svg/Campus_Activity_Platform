from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCalendarWidget,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.checkin_controller import CheckinController
from controllers.statistics_controller import StatisticsController
from services.interfaces.checkin_service import CheckinRecordDTO
from services.interfaces.statistics_service import ActivityCalendarEventDTO, ParticipantStatisticsDTO
from ui.widgets.table_utils import configure_table, set_row_height


class ParticipantCenterView(QWidget):
    def __init__(
        self,
        checkin_controller: CheckinController,
        statistics_controller: StatisticsController | None = None,
    ) -> None:
        super().__init__()
        self._checkin_controller = checkin_controller
        self._statistics_controller = statistics_controller
        self._calendar_events: list[ActivityCalendarEventDTO] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("我的签到")
        title.setObjectName("pageTitle")

        self._statistics_layout = QGridLayout()
        self._statistics_layout.setSpacing(10)

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)

        self._empty_label = QLabel("暂无签到记录")
        self._empty_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["活动标题", "签到状态", "签到方式", "签到时间", "地点信息", "修正原因"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        self._calendar = QCalendarWidget()
        self._calendar.selectionChanged.connect(self._render_selected_date_events)
        self._calendar_label = QLabel("请选择日期查看活动安排")
        self._calendar_label.setObjectName("placeholderHint")

        layout.addWidget(title)
        layout.addLayout(self._statistics_layout)
        layout.addWidget(refresh_button)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table, 1)
        layout.addWidget(QLabel("我的活动日历"))
        layout.addWidget(self._calendar)
        layout.addWidget(self._calendar_label)

        self.refresh()

    def refresh(self) -> None:
        self._load_statistics()
        self._load_calendar_events()
        result = self._checkin_controller.list_my_checkins()
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render(result.checkins or [])

    def _render(self, checkins: list[CheckinRecordDTO]) -> None:
        self._table.setRowCount(len(checkins))
        self._empty_label.setVisible(len(checkins) == 0)
        self._table.setVisible(len(checkins) > 0)
        for row, item in enumerate(checkins):
            set_row_height(self._table, row)
            values = [
                item.activity_title,
                self._status_text(item.status),
                item.checkin_method,
                "" if item.checkin_time is None else item.checkin_time.strftime("%Y-%m-%d %H:%M"),
                item.location_info,
                item.correction_reason,
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))
        self._table.resizeColumnsToContents()

    def _load_statistics(self) -> None:
        if self._statistics_controller is None:
            return
        result = self._statistics_controller.get_participant_statistics()
        if not result.success or result.participant_statistics is None:
            return
        self._render_statistics(result.participant_statistics)

    def _render_statistics(self, statistics: ParticipantStatisticsDTO) -> None:
        while self._statistics_layout.count():
            item = self._statistics_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        cards = [
            ("我的报名数", statistics.registration_count),
            ("我的签到数", statistics.checkin_count),
            ("我的评价数", statistics.review_count),
            ("我的证书数", statistics.certificate_count),
            ("获得学分", f"{statistics.earned_credit:g}"),
            ("志愿时长", f"{statistics.volunteer_hours:g}"),
        ]
        for index, (label, value) in enumerate(cards):
            card = QLabel(f"{label}\n{value}")
            card.setObjectName("statCard")
            self._statistics_layout.addWidget(card, index // 3, index % 3)

    def _load_calendar_events(self) -> None:
        if self._statistics_controller is None:
            return
        result = self._statistics_controller.list_participant_calendar_events()
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
            self._calendar_label.setText("所选日期暂无报名活动")
            return
        lines = [
            f"{event.start_time.strftime('%H:%M')} {event.title}（{event.status}，{event.location}）"
            for event in matched
        ]
        self._calendar_label.setText("\n".join(lines))

    def _status_text(self, status: str) -> str:
        return {"checked_in": "已签到", "absent": "未签到", "corrected": "补签"}.get(status, status)
