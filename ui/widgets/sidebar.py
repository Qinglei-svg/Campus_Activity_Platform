from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


class Sidebar(QFrame):
    menu_selected = Signal(str)

    def __init__(self, menus: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self._buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(10)

        title = QLabel("功能菜单")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)
        layout.addSpacing(8)

        for menu_name in menus:
            button = QPushButton(menu_name)
            button.setObjectName("menuButton")
            button.setProperty("active", False)
            button.clicked.connect(lambda checked=False, name=menu_name: self.select_menu(name))
            layout.addWidget(button)
            self._buttons[menu_name] = button

        layout.addStretch(1)

        if menus:
            self.select_menu(menus[0], emit_signal=False)

    def select_menu(self, menu_name: str, emit_signal: bool = True) -> None:
        for name, button in self._buttons.items():
            button.setProperty("active", name == menu_name)
            button.style().unpolish(button)
            button.style().polish(button)

        if emit_signal:
            self.menu_selected.emit(menu_name)
