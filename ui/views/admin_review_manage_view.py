from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.review_controller import ReviewController
from services.interfaces.review_service import ReviewDTO
from ui.widgets.table_utils import apply_table_column_resize, configure_table, set_row_height, set_table_buttons, table_button


class AdminReviewManageView(QWidget):
    def __init__(self, review_controller: ReviewController) -> None:
        super().__init__()
        self._review_controller = review_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("评价管理")
        title.setObjectName("pageTitle")

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)

        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(["活动标题", "用户账号", "用户姓名", "整体评分", "文字评价", "状态", "评价时间", "操作"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addWidget(refresh_button)
        layout.addWidget(self._table, 1)
        self.refresh()

    def refresh(self) -> None:
        result = self._review_controller.list_admin_reviews()
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render_reviews(result.reviews or [])

    def _render_reviews(self, reviews: list[ReviewDTO]) -> None:
        self._table.setRowCount(len(reviews))
        for row, review in enumerate(reviews):
            set_row_height(self._table, row)
            values = [
                review.activity_title,
                review.user_account,
                review.user_name,
                f"{review.overall_score:g}",
                review.comment,
                review.status,
                review.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            delete_button = table_button(
                "删除违规评价",
                lambda review_id=review.review_id: self._delete_review(review_id),
                danger=True,
            )
            set_table_buttons(self._table, row, 7, delete_button)
        apply_table_column_resize(self._table)

    def _delete_review(self, review_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除该违规评价吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        result = self._review_controller.delete_review(review_id)
        if not result.success:
            QMessageBox.warning(self, "删除失败", result.message)
            return
        QMessageBox.information(self, "删除成功", result.message)
        self.refresh()
