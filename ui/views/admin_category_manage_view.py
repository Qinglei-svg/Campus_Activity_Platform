from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.category_controller import CategoryController
from services.interfaces.category_service import ActivityCategoryManageDTO
from ui.widgets.table_utils import (
    apply_table_column_resize,
    configure_table,
    set_row_height,
    set_table_buttons,
    table_button,
)


class AdminCategoryManageView(QWidget):
    def __init__(self, category_controller: CategoryController) -> None:
        super().__init__()
        self._category_controller = category_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("活动分类")
        title.setObjectName("pageTitle")

        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("分类名称")
        self._description_input = QLineEdit()
        self._description_input.setPlaceholderText("分类描述")

        add_button = QPushButton("新增分类")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self._create_category)

        clear_button = QPushButton("清空")
        clear_button.clicked.connect(self._clear_form)

        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh)

        form_layout.addWidget(self._name_input, 2)
        form_layout.addWidget(self._description_input, 4)
        form_layout.addWidget(add_button)
        form_layout.addWidget(clear_button)
        form_layout.addWidget(refresh_button)

        self._hint_label = QLabel("禁用分类后，发布者创建活动时将无法继续选择；历史活动仍保留原分类名称。")
        self._hint_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["分类名称", "描述", "状态", "活动数量", "创建时间", "编辑", "启用状态"]
        )
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        self._empty_label = QLabel("暂无活动分类")
        self._empty_label.setObjectName("placeholderHint")

        layout.addWidget(title)
        layout.addLayout(form_layout)
        layout.addWidget(self._hint_label)
        layout.addWidget(self._table, 1)
        layout.addWidget(self._empty_label)

        self.refresh()

    def refresh(self) -> None:
        result = self._category_controller.list_categories()
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render(result.categories or [])

    def _create_category(self) -> None:
        result = self._category_controller.create_category(
            self._name_input.text(),
            self._description_input.text(),
        )
        if not result.success:
            QMessageBox.warning(self, "新增失败", result.message)
            return

        QMessageBox.information(self, "新增成功", result.message)
        self._clear_form()
        self.refresh()

    def _render(self, categories: list[ActivityCategoryManageDTO]) -> None:
        self._empty_label.setVisible(not categories)
        self._table.setVisible(bool(categories))
        self._table.setRowCount(len(categories))
        for row, category in enumerate(categories):
            set_row_height(self._table, row)
            values = [
                category.name,
                category.description,
                "启用" if category.enabled else "禁用",
                str(category.activity_count),
                category.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            edit_button = table_button("编辑", lambda item=category: self._edit_category(item))

            status_button = table_button(
                "禁用" if category.enabled else "启用",
                lambda item=category: self._toggle_category(item),
                danger=category.enabled,
            )
            set_table_buttons(self._table, row, 5, edit_button)
            set_table_buttons(self._table, row, 6, status_button)

        apply_table_column_resize(self._table, tail_action_columns=2)

    def _edit_category(self, category: ActivityCategoryManageDTO) -> None:
        name, ok = QInputDialog.getText(self, "编辑分类", "分类名称：", text=category.name)
        if not ok:
            return

        description, ok = QInputDialog.getMultiLineText(
            self,
            "编辑分类",
            "分类描述：",
            category.description,
        )
        if not ok:
            return

        result = self._category_controller.update_category(
            category.category_id,
            name,
            description,
        )
        if not result.success:
            QMessageBox.warning(self, "保存失败", result.message)
            return
        QMessageBox.information(self, "保存成功", result.message)
        self.refresh()

    def _toggle_category(self, category: ActivityCategoryManageDTO) -> None:
        if category.enabled:
            confirm = QMessageBox.question(
                self,
                "确认禁用",
                f"确认禁用分类【{category.name}】吗？历史活动仍会保留该分类名称。",
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            result = self._category_controller.disable_category(category.category_id)
        else:
            result = self._category_controller.enable_category(category.category_id)

        if not result.success:
            QMessageBox.warning(self, "操作失败", result.message)
            return
        QMessageBox.information(self, "操作成功", result.message)
        self.refresh()

    def _clear_form(self) -> None:
        self._name_input.clear()
        self._description_input.clear()
