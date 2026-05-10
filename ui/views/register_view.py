from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.settings import APP_NAME, LOGIN_WINDOW_HEIGHT, LOGIN_WINDOW_WIDTH
from controllers.auth_controller import AuthController


class RegisterView(QWidget):
    back_to_login_requested = Signal()

    def __init__(self, auth_controller: AuthController) -> None:
        super().__init__()
        self._auth_controller = auth_controller
        self.setWindowTitle(f"{APP_NAME} - 用户注册")
        self.resize(LOGIN_WINDOW_WIDTH, LOGIN_WINDOW_HEIGHT)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(40, 40, 40, 40)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        panel = QFrame()
        panel.setObjectName("loginPanel")
        panel.setMaximumWidth(520)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(42, 40, 42, 40)
        panel_layout.setSpacing(16)

        title = QLabel("用户注册")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._account_input = QLineEdit()
        self._account_input.setPlaceholderText("请输入账号")

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("请输入姓名")

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("请输入密码")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self._confirm_password_input = QLineEdit()
        self._confirm_password_input.setPlaceholderText("请再次输入密码")
        self._confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self._phone_input = QLineEdit()
        self._phone_input.setPlaceholderText("请输入手机号")

        register_button = QPushButton("注册")
        register_button.setObjectName("primaryButton")
        register_button.clicked.connect(self._handle_register)

        back_button = QPushButton("返回登录")
        back_button.clicked.connect(self.back_to_login_requested.emit)

        panel_layout.addWidget(title)
        panel_layout.addSpacing(8)
        panel_layout.addWidget(self._account_input)
        panel_layout.addWidget(self._name_input)
        panel_layout.addWidget(self._password_input)
        panel_layout.addWidget(self._confirm_password_input)
        panel_layout.addWidget(self._phone_input)
        panel_layout.addWidget(register_button)
        panel_layout.addWidget(back_button)

        outer_layout.addWidget(panel)

    def reset_form(self) -> None:
        self._account_input.clear()
        self._name_input.clear()
        self._password_input.clear()
        self._confirm_password_input.clear()
        self._phone_input.clear()

    def _handle_register(self) -> None:
        password = self._password_input.text()
        confirm_password = self._confirm_password_input.text()
        if password != confirm_password:
            QMessageBox.warning(self, "注册失败", "两次输入的密码不一致。")
            return

        result = self._auth_controller.register(
            account=self._account_input.text(),
            name=self._name_input.text(),
            password=password,
            phone=self._phone_input.text(),
        )
        if not result.success:
            QMessageBox.warning(self, "注册失败", result.message)
            return

        QMessageBox.information(self, "注册成功", "注册成功，请返回登录。")
        self.reset_form()
        self.back_to_login_requested.emit()
