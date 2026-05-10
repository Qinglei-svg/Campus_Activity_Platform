from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.statistics_controller import StatisticsController
from services.interfaces.statistics_service import AdminStatisticsDTO
from ui.widgets.table_utils import configure_table, set_row_height


class AdminStatisticsView(QWidget):
    def __init__(self, statistics_controller: StatisticsController) -> None:
        super().__init__()
        self._statistics_controller = statistics_controller

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(14)

        title = QLabel("数据统计")
        title.setObjectName("pageTitle")

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)

        self._cards = QGridLayout()
        self._cards.setSpacing(10)

        category_title = QLabel("分类活动数量")
        category_title.setObjectName("roleLabel")
        self._category_table = QTableWidget(0, 2)
        self._category_table.setHorizontalHeaderLabels(["活动分类", "活动数量"])
        self._category_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._category_table.verticalHeader().setVisible(False)
        self._category_table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._category_table)

        hot_title = QLabel("热门活动排行")
        hot_title.setObjectName("roleLabel")
        self._hot_table = QTableWidget(0, 5)
        self._hot_table.setHorizontalHeaderLabels(["活动标题", "分类", "发布者", "报名数", "签到数"])
        self._hot_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._hot_table.verticalHeader().setVisible(False)
        self._hot_table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._hot_table)

        self._layout.addWidget(title)
        self._layout.addWidget(refresh_button)
        self._layout.addLayout(self._cards)
        self._layout.addWidget(category_title)
        self._layout.addWidget(self._category_table)
        self._layout.addWidget(hot_title)
        self._layout.addWidget(self._hot_table)
        self.refresh()

    def refresh(self) -> None:
        result = self._statistics_controller.get_admin_statistics()
        if not result.success or result.admin_statistics is None:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render(result.admin_statistics)

    def _render(self, statistics: AdminStatisticsDTO) -> None:
        self._clear_cards()
        cards = [
            ("总用户数", statistics.total_users),
            ("总活动数", statistics.total_activities),
            ("总报名数", statistics.total_registrations),
            ("总签到数", statistics.total_checkins),
            ("总评价数", statistics.total_reviews),
            ("总证书数", statistics.total_certificates),
        ]
        for index, (label, value) in enumerate(cards):
            card = QLabel(f"{label}\n{value}")
            card.setObjectName("statCard")
            self._cards.addWidget(card, index // 3, index % 3)

        self._category_table.setRowCount(len(statistics.category_counts))
        for row, item in enumerate(statistics.category_counts):
            set_row_height(self._category_table, row)
            self._category_table.setItem(row, 0, QTableWidgetItem(item.category_name))
            self._category_table.setItem(row, 1, QTableWidgetItem(str(item.activity_count)))
        self._category_table.resizeColumnsToContents()

        self._hot_table.setRowCount(len(statistics.hot_activities))
        for row, item in enumerate(statistics.hot_activities):
            set_row_height(self._hot_table, row)
            values = [
                item.title,
                item.category_name,
                item.publisher_name,
                str(item.registration_count),
                str(item.checkin_count),
            ]
            for column, value in enumerate(values):
                self._hot_table.setItem(row, column, QTableWidgetItem(value))
        self._hot_table.resizeColumnsToContents()

    def _clear_cards(self) -> None:
        while self._cards.count():
            item = self._cards.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
