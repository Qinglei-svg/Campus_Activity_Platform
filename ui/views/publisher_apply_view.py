from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from controllers.user_controller import UserController


class PublisherApplyView(QWidget):
    def __init__(self, user_controller: UserController) -> None:
        super().__init__()
        self._user_controller = user_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("申请发布者")
        title.setObjectName("pageTitle")

        form = QFormLayout()
        self._organization_input = QLineEdit()
        self._responsible_person_input = QLineEdit()
        self._contact_input = QLineEdit()
        self._note_input = QTextEdit()

        form.addRow("组织名称：", self._organization_input)
        form.addRow("负责人：", self._responsible_person_input)
        form.addRow("联系方式：", self._contact_input)
        form.addRow("申请说明：", self._note_input)

        submit_button = QPushButton("提交申请")
        submit_button.setObjectName("primaryButton")
        submit_button.clicked.connect(self._submit)

        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(submit_button)
        layout.addStretch(1)

    def _submit(self) -> None:
        result = self._user_controller.submit_publisher_application(
            {
                "organization_name": self._organization_input.text(),
                "responsible_person": self._responsible_person_input.text(),
                "contact_info": self._contact_input.text(),
                "application_note": self._note_input.toPlainText(),
            }
        )
        if not result.success:
            QMessageBox.warning(self, "提交失败", result.message)
            return
        QMessageBox.information(self, "提交成功", result.message)
        self._organization_input.clear()
        self._responsible_person_input.clear()
        self._contact_input.clear()
        self._note_input.clear()
