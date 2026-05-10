from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderView(QWidget):
    def __init__(self, page_name: str) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(14)

        title = QLabel(f"当前页面：{page_name}")
        title.setObjectName("pageTitle")

        hint = QLabel("此处为占位页面，后续阶段将逐步实现具体功能。")
        hint.setObjectName("placeholderHint")

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addStretch(1)
