from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QHBoxLayout, QWidget


class TopBar(QFrame):
    logout_requested = Signal()

    def __init__(self, user_name: str, role_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("topbar")
        self.setFixedHeight(72)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        self._role_label = QLabel(f"当前用户：{user_name}    当前角色：{role_name}")
        self._role_label.setObjectName("roleLabel")

        logout_button = QPushButton("退出登录")
        logout_button.setObjectName("dangerButton")
        logout_button.clicked.connect(self.logout_requested.emit)

        layout.addWidget(self._role_label)
        layout.addStretch(1)
        layout.addWidget(logout_button)
