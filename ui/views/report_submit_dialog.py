from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)


class ReportSubmitDialog(QDialog):
    def __init__(self, title: str, target_text: str, submit_callback) -> None:
        super().__init__()
        self._submit_callback = submit_callback
        self.setWindowTitle(title)
        self.resize(420, 260)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        target_label = QLabel(target_text)
        target_label.setWordWrap(True)

        self._reason_input = QPlainTextEdit()
        self._reason_input.setPlaceholderText("请输入举报原因")

        submit_button = QPushButton("提交举报")
        submit_button.setObjectName("primaryButton")
        submit_button.clicked.connect(self._submit)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)

        layout.addWidget(target_label)
        layout.addWidget(self._reason_input, 1)
        layout.addWidget(submit_button)
        layout.addWidget(cancel_button)

    def _submit(self) -> None:
        result = self._submit_callback(self._reason_input.toPlainText())
        if not result.success:
            QMessageBox.warning(self, "提交失败", result.message)
            return
        QMessageBox.information(self, "提交成功", result.message)
        self.accept()
