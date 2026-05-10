from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTableWidget,
    QWidget,
)


TABLE_ROW_HEIGHT = 52


class _TableItemNoFocusDelegate(QStyledItemDelegate):
    """关闭单元格焦点框绘制。选中行时 Windows 风格常在每个格左侧画一条蓝竖线。"""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.state &= ~QStyle.StateFlag.State_HasFocus
        super().paint(painter, opt, index)


def configure_table(table: QTableWidget) -> None:
    table.setAlternatingRowColors(True)
    table.setWordWrap(False)
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
    table.verticalHeader().setMinimumSectionSize(TABLE_ROW_HEIGHT)
    table.setItemDelegate(_TableItemNoFocusDelegate(table))


def apply_table_column_resize(table: QTableWidget, *, tail_action_columns: int = 1) -> None:
    """数据刷新后调整列宽：左侧为文本列；右侧连续「操作列」按控件实际宽度固定列宽，避免 Stretch 被正文列挤得过窄。

    纯文本的尾列（无 cellWidget）仍用 Stretch 吃掉剩余宽度。
    """
    header = table.horizontalHeader()
    n = table.columnCount()
    if n <= 0:
        return

    k = max(1, min(tail_action_columns, n))

    if n == 1:
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        return

    text_cols = n - k
    if text_cols <= 0:
        for i in range(n):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        return

    for i in range(text_cols):
        header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    cell_horizontal_margin = 24
    for i in range(text_cols, n):
        max_need = 0
        for row in range(table.rowCount()):
            cw = table.cellWidget(row, i)
            if cw is not None:
                max_need = max(max_need, cw.minimumSizeHint().width())
        if max_need > 0:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(i, max_need + cell_horizontal_margin)
        else:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)


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
    fm = button.fontMetrics()
    button.setMinimumWidth(max(96, fm.horizontalAdvance(text) + 36))
    button.clicked.connect(lambda checked=False: callback())
    return button


def table_action_cell(*buttons: QPushButton) -> QWidget:
    cell = QWidget()
    cell.setObjectName("tableActionCell")
    layout = QHBoxLayout(cell)
    layout.setContentsMargins(6, 4, 6, 4)
    layout.setSpacing(8)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if len(buttons) <= 1:
        layout.addStretch(1)
        for button in buttons:
            layout.addWidget(button)
        layout.addStretch(1)
    else:
        for button in buttons:
            layout.addWidget(button)
        margin_w = layout.contentsMargins().left() + layout.contentsMargins().right()
        spacing = max(layout.spacing(), 0)
        min_inner = sum(max(b.minimumWidth(), b.sizeHint().width()) for b in buttons)
        min_inner += spacing * max(0, len(buttons) - 1)
        cell.setMinimumWidth(margin_w + min_inner)
    return cell


def set_table_buttons(table: QTableWidget, row: int, column: int, *buttons: QPushButton) -> None:
    set_row_height(table, row)
    table.setCellWidget(row, column, table_action_cell(*buttons))
