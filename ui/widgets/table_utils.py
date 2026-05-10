from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTableWidget, QWidget


TABLE_ROW_HEIGHT = 52


def configure_table(table: QTableWidget) -> None:
    table.setAlternatingRowColors(True)
    table.setWordWrap(False)
    table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
    table.verticalHeader().setMinimumSectionSize(TABLE_ROW_HEIGHT)


def set_row_height(table: QTableWidget, row: int) -> None:
    table.setRowHeight(row, TABLE_ROW_HEIGHT)


def table_button(
    text: str,
    callback: Callable[[], None],
    *,
    danger: bool = False,
    enabled: bool = True,
) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("tableDangerButton" if danger else "tableButton")
    button.setEnabled(enabled)
    button.clicked.connect(lambda checked=False: callback())
    return button


def table_action_cell(*buttons: QPushButton) -> QWidget:
    cell = QWidget()
    cell.setObjectName("tableActionCell")
    layout = QHBoxLayout(cell)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(6)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addStretch(1)
    for button in buttons:
        layout.addWidget(button)
    layout.addStretch(1)
    return cell


def set_table_buttons(table: QTableWidget, row: int, column: int, *buttons: QPushButton) -> None:
    set_row_height(table, row)
    table.setCellWidget(row, column, table_action_cell(*buttons))
