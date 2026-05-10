from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.settings import APP_NAME, APP_SUBTITLE, LOGIN_WINDOW_HEIGHT, LOGIN_WINDOW_WIDTH
from controllers.auth_controller import AuthController
from services.interfaces.auth_service import AuthenticatedUser


class LoginView(QWidget):
    login_succeeded = Signal(object)
    register_requested = Signal()

    def __init__(self, auth_controller: AuthController) -> None:
        super().__init__()
        self._auth_controller = auth_controller
        self.setWindowTitle(APP_NAME)
        self.resize(LOGIN_WINDOW_WIDTH, LOGIN_WINDOW_HEIGHT)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(40, 40, 40, 40)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        panel = QFrame()
        panel.setObjectName("loginPanel")
        panel.setMaximumWidth(520)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(42, 40, 42, 40)
        panel_layout.setSpacing(18)

        title = QLabel(APP_NAME)
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(APP_SUBTITLE)
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._account_input = QLineEdit()
        self._account_input.setPlaceholderText("请输入账号")

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("请输入密码")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_button = QPushButton("登录")
        login_button.setObjectName("primaryButton")
        login_button.clicked.connect(self._handle_login)

        register_button = QPushButton("注册新账号")
        register_button.clicked.connect(self.register_requested.emit)

        quick_login_layout = QGridLayout()
        quick_login_layout.setHorizontalSpacing(10)
        quick_login_layout.setVerticalSpacing(10)

        admin_button = QPushButton("管理员快速登录")
        publisher_button = QPushButton("发布者快速登录")
        participant_button = QPushButton("参与者快速登录")

        admin_button.clicked.connect(lambda: self._quick_login("admin", "admin123"))
        publisher_button.clicked.connect(lambda: self._quick_login("publisher", "publisher123"))
        participant_button.clicked.connect(lambda: self._quick_login("student", "student123"))

        quick_login_layout.addWidget(admin_button, 0, 0)
        quick_login_layout.addWidget(publisher_button, 0, 1)
        quick_login_layout.addWidget(participant_button, 1, 0, 1, 2)

        panel_layout.addWidget(title)
        panel_layout.addWidget(subtitle)
        panel_layout.addSpacing(10)
        panel_layout.addWidget(self._account_input)
        panel_layout.addWidget(self._password_input)
        panel_layout.addWidget(login_button)
        panel_layout.addWidget(register_button)
        panel_layout.addSpacing(6)
        panel_layout.addLayout(quick_login_layout)

        outer_layout.addWidget(panel)

    def reset_form(self) -> None:
        self._account_input.clear()
        self._password_input.clear()

    def _handle_login(self) -> None:
        self._login(self._account_input.text(), self._password_input.text())

    def _quick_login(self, account: str, password: str) -> None:
        self._account_input.setText(account)
        self._password_input.setText(password)
        self._login(account, password)

    def _login(self, account: str, password: str) -> None:
        result = self._auth_controller.login(account, password)
        if not result.success or result.user is None:
            QMessageBox.warning(self, "登录失败", result.message)
            return

        self.login_succeeded.emit(result.user)
