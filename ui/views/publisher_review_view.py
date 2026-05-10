from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.activity_controller import ActivityController
from controllers.review_controller import ReviewController
from services.interfaces.review_service import ReviewDTO
from ui.widgets.table_utils import apply_table_column_resize, configure_table, set_row_height


class PublisherReviewView(QWidget):
    def __init__(self, activity_controller: ActivityController, review_controller: ReviewController) -> None:
        super().__init__()
        self._activity_controller = activity_controller
        self._review_controller = review_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("活动评价")
        title.setObjectName("pageTitle")

        self._activity_combo = QComboBox()
        self._summary_label = QLabel("平均评分：暂无评价")
        self._summary_label.setObjectName("placeholderHint")

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)

        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(["用户账号", "用户姓名", "内容质量", "组织安排", "现场体验", "整体满意", "文字评价", "评价时间"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addWidget(self._activity_combo)
        layout.addWidget(refresh_button)
        layout.addWidget(self._summary_label)
        layout.addWidget(self._table, 1)

        self._load_activities()
        self._activity_combo.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def _load_activities(self) -> None:
        result = self._activity_controller.list_my_activities()
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._activity_combo.clear()
        for activity in result.activities or []:
            self._activity_combo.addItem(f"{activity.title}（{activity.status}）", activity.activity_id)

    def refresh(self) -> None:
        activity_id = self._activity_combo.currentData()
        if activity_id is None:
            self._table.setRowCount(0)
            return
        result = self._review_controller.list_activity_reviews(activity_id)
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render_reviews(result.reviews or [])
        summary = result.summary
        if summary and summary.count:
            self._summary_label.setText(
                f"平均评分：内容 {summary.average_content_score:.1f}，组织 {summary.average_organization_score:.1f}，"
                f"体验 {summary.average_experience_score:.1f}，整体 {summary.average_overall_score:.1f}"
            )
        else:
            self._summary_label.setText("平均评分：暂无评价")

    def _render_reviews(self, reviews: list[ReviewDTO]) -> None:
        self._table.setRowCount(len(reviews))
        for row, review in enumerate(reviews):
            set_row_height(self._table, row)
            values = [
                review.user_account,
                review.user_name,
                f"{review.content_score:g}",
                f"{review.organization_score:g}",
                f"{review.experience_score:g}",
                f"{review.overall_score:g}",
                review.comment,
                review.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))
        apply_table_column_resize(self._table)
