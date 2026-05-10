from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from controllers.review_controller import ReviewController


class ReviewSubmitDialog(QDialog):
    def __init__(self, activity_id: int, review_controller: ReviewController) -> None:
        super().__init__()
        self._activity_id = activity_id
        self._review_controller = review_controller
        self.setWindowTitle("提交活动评价")
        self.resize(420, 360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._content_score = self._score_spinbox()
        self._organization_score = self._score_spinbox()
        self._experience_score = self._score_spinbox()
        self._overall_score = self._score_spinbox()
        self._comment_input = QTextEdit()

        form.addRow("内容质量评分：", self._content_score)
        form.addRow("组织安排评分：", self._organization_score)
        form.addRow("现场体验评分：", self._experience_score)
        form.addRow("整体满意度评分：", self._overall_score)
        form.addRow("文字评价：", self._comment_input)

        submit_button = QPushButton("提交评价")
        submit_button.setObjectName("primaryButton")
        submit_button.clicked.connect(self._submit)

        layout.addLayout(form)
        layout.addWidget(submit_button)

    def _score_spinbox(self) -> QSpinBox:
        spinbox = QSpinBox()
        spinbox.setRange(1, 5)
        spinbox.setValue(5)
        return spinbox

    def _submit(self) -> None:
        result = self._review_controller.submit_review(
            self._activity_id,
            {
                "content_score": self._content_score.value(),
                "organization_score": self._organization_score.value(),
                "experience_score": self._experience_score.value(),
                "overall_score": self._overall_score.value(),
                "comment": self._comment_input.toPlainText(),
            },
        )
        if not result.success:
            QMessageBox.warning(self, "提交失败", result.message)
            return
        QMessageBox.information(self, "提交成功", result.message)
        self.accept()
