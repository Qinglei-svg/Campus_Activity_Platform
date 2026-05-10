from __future__ import annotations

from PySide6.QtCore import Signal
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

from controllers.activity_controller import ActivityController
from services.interfaces.activity_service import ActivityDTO
from ui.widgets.table_utils import apply_table_column_resize, configure_table, set_row_height, set_table_buttons, table_button


class ActivityHallView(QWidget):
    detail_requested = Signal(int)

    def __init__(self, activity_controller: ActivityController) -> None:
        super().__init__()
        self._activity_controller = activity_controller
        self._activity_ids: list[int] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("活动大厅")
        title.setObjectName("pageTitle")

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self._keyword_input = QLineEdit()
        self._keyword_input.setPlaceholderText("请输入活动标题关键词")

        self._category_combo = QComboBox()
        self._category_combo.addItem("全部分类", None)

        search_button = QPushButton("搜索")
        search_button.setObjectName("primaryButton")
        search_button.clicked.connect(self.refresh)

        reset_button = QPushButton("重置")
        reset_button.clicked.connect(self._reset_filters)

        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh)

        filter_layout.addWidget(self._keyword_input, 2)
        filter_layout.addWidget(self._category_combo, 1)
        filter_layout.addWidget(search_button)
        filter_layout.addWidget(reset_button)
        filter_layout.addWidget(refresh_button)

        self._empty_label = QLabel("暂无已上线活动")
        self._empty_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 9)
        self._table.setHorizontalHeaderLabels(
            ["活动标题", "活动分类", "主办方", "活动时间", "活动地点", "剩余名额", "学分", "志愿时长", "操作"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addLayout(filter_layout)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table, 1)

        self._load_categories()
        self.refresh()

    def refresh(self) -> None:
        category_id = self._category_combo.currentData()
        result = self._activity_controller.list_online_activities(
            keyword=self._keyword_input.text().strip() or None,
            category_id=category_id,
        )
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render_activities(result.activities or [])

    def _load_categories(self) -> None:
        result = self._activity_controller.list_categories()
        if not result.success:
            QMessageBox.warning(self, "分类加载失败", result.message)
            return
        for category in result.categories or []:
            self._category_combo.addItem(category.name, category.category_id)

    def _reset_filters(self) -> None:
        self._keyword_input.clear()
        self._category_combo.setCurrentIndex(0)
        self.refresh()

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
                str(activity.remaining_count),
                f"{activity.credit:g}",
                f"{activity.volunteer_hours:g}",
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            detail_button = table_button(
                "查看详情",
                lambda activity_id=activity.activity_id: self.detail_requested.emit(activity_id),
            )
            set_table_buttons(self._table, row, 8, detail_button)

        apply_table_column_resize(self._table)
