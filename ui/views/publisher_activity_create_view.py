from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDateTime, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from controllers.activity_controller import ActivityController
from services.interfaces.activity_service import ActivityDTO


class PublisherActivityCreateView(QWidget):
    saved = Signal()
    submitted = Signal()

    def __init__(
        self,
        activity_controller: ActivityController,
        activity: ActivityDTO | None = None,
    ) -> None:
        super().__init__()
        self._activity_controller = activity_controller
        self._editing_activity_id: int | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self._title_label = QLabel("创建活动")
        self._title_label.setObjectName("pageTitle")

        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(16)

        self._title_input = QLineEdit()
        self._category_combo = QComboBox()
        self._start_time_input = QDateTimeEdit()
        self._end_time_input = QDateTimeEdit()
        self._signup_start_time_input = QDateTimeEdit()
        self._signup_end_time_input = QDateTimeEdit()
        self._location_input = QLineEdit()
        self._capacity_input = QSpinBox()
        self._credit_input = QDoubleSpinBox()
        self._volunteer_hours_input = QDoubleSpinBox()
        self._description_input = QTextEdit()
        self._need_signup_audit_input = QCheckBox("需要审核报名")

        for date_time_input in (
            self._start_time_input,
            self._end_time_input,
            self._signup_start_time_input,
            self._signup_end_time_input,
        ):
            date_time_input.setCalendarPopup(True)
            date_time_input.setDisplayFormat("yyyy-MM-dd HH:mm")

        self._capacity_input.setRange(1, 100000)
        self._credit_input.setRange(0, 100)
        self._credit_input.setDecimals(1)
        self._volunteer_hours_input.setRange(0, 1000)
        self._volunteer_hours_input.setDecimals(1)

        form.addRow("活动标题：", self._title_input)
        form.addRow("活动分类：", self._category_combo)
        form.addRow("活动开始时间：", self._start_time_input)
        form.addRow("活动结束时间：", self._end_time_input)
        form.addRow("报名开始时间：", self._signup_start_time_input)
        form.addRow("报名结束时间：", self._signup_end_time_input)
        form.addRow("活动地点：", self._location_input)
        form.addRow("人数上限：", self._capacity_input)
        form.addRow("学分：", self._credit_input)
        form.addRow("志愿时长：", self._volunteer_hours_input)
        form.addRow("活动详情：", self._description_input)
        form.addRow("", self._need_signup_audit_input)

        button_layout = QHBoxLayout()
        save_button = QPushButton("保存草稿")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self._save_draft)

        submit_button = QPushButton("保存并提交审核")
        submit_button.clicked.connect(self._save_and_submit)

        clear_button = QPushButton("清空表单")
        clear_button.clicked.connect(self.clear_form)

        button_layout.addWidget(save_button)
        button_layout.addWidget(submit_button)
        button_layout.addWidget(clear_button)
        button_layout.addStretch(1)

        layout.addWidget(self._title_label)
        layout.addLayout(form)
        layout.addLayout(button_layout)

        self._load_categories()
        self.clear_form()
        if activity is not None:
            self.set_activity(activity)

    def set_activity(self, activity: ActivityDTO) -> None:
        self._editing_activity_id = activity.activity_id
        self._title_label.setText("编辑活动草稿")
        self._title_input.setText(activity.title)
        self._set_category(activity.category_id)
        self._start_time_input.setDateTime(self._from_datetime(activity.start_time))
        self._end_time_input.setDateTime(self._from_datetime(activity.end_time))
        self._signup_start_time_input.setDateTime(self._from_datetime(activity.signup_start_time))
        self._signup_end_time_input.setDateTime(self._from_datetime(activity.signup_end_time))
        self._location_input.setText(activity.location)
        self._capacity_input.setValue(activity.capacity)
        self._credit_input.setValue(activity.credit)
        self._volunteer_hours_input.setValue(activity.volunteer_hours)
        self._description_input.setPlainText(activity.description)
        self._need_signup_audit_input.setChecked(activity.need_signup_audit)

    def clear_form(self) -> None:
        self._editing_activity_id = None
        self._title_label.setText("创建活动")
        self._title_input.clear()
        self._category_combo.setCurrentIndex(0)
        now = QDateTime.currentDateTime()
        self._signup_start_time_input.setDateTime(now)
        self._signup_end_time_input.setDateTime(now.addDays(5))
        self._start_time_input.setDateTime(now.addDays(7))
        self._end_time_input.setDateTime(now.addDays(7).addSecs(7200))
        self._location_input.clear()
        self._capacity_input.setValue(50)
        self._credit_input.setValue(0)
        self._volunteer_hours_input.setValue(0)
        self._description_input.clear()
        self._need_signup_audit_input.setChecked(False)

    def _load_categories(self) -> None:
        self._category_combo.clear()
        self._category_combo.addItem("请选择分类", None)
        result = self._activity_controller.list_categories()
        if not result.success:
            QMessageBox.warning(self, "分类加载失败", result.message)
            return
        for category in result.categories or []:
            self._category_combo.addItem(category.name, category.category_id)

    def _collect_data(self) -> dict[str, object]:
        return {
            "title": self._title_input.text(),
            "category_id": self._category_combo.currentData(),
            "start_time": self._to_datetime(self._start_time_input),
            "end_time": self._to_datetime(self._end_time_input),
            "signup_start_time": self._to_datetime(self._signup_start_time_input),
            "signup_end_time": self._to_datetime(self._signup_end_time_input),
            "location": self._location_input.text(),
            "capacity": self._capacity_input.value(),
            "credit": self._credit_input.value(),
            "volunteer_hours": self._volunteer_hours_input.value(),
            "description": self._description_input.toPlainText(),
            "need_signup_audit": self._need_signup_audit_input.isChecked(),
        }

    def _save_draft(self) -> None:
        result = self._save_current_form()
        if not result:
            return
        QMessageBox.information(self, "保存成功", "草稿保存成功")
        self.saved.emit()

    def _save_and_submit(self) -> None:
        result = self._save_current_form()
        if result is None or result.activity is None:
            return
        submit_result = self._activity_controller.submit_activity(result.activity.activity_id)
        if not submit_result.success:
            QMessageBox.warning(self, "提交失败", submit_result.message)
            return
        QMessageBox.information(self, "提交成功", "活动已提交审核")
        self.submitted.emit()
        self.clear_form()

    def _save_current_form(self):
        data = self._collect_data()
        if self._editing_activity_id is None:
            result = self._activity_controller.create_draft(data)
        else:
            result = self._activity_controller.update_activity(self._editing_activity_id, data)
        if not result.success:
            QMessageBox.warning(self, "保存失败", result.message)
            return None
        if result.activity is not None:
            self._editing_activity_id = result.activity.activity_id
        return result

    def _set_category(self, category_id: int) -> None:
        for index in range(self._category_combo.count()):
            if self._category_combo.itemData(index) == category_id:
                self._category_combo.setCurrentIndex(index)
                return

    def _to_datetime(self, editor: QDateTimeEdit) -> datetime:
        return editor.dateTime().toPython()

    def _from_datetime(self, value: datetime) -> QDateTime:
        return QDateTime.fromSecsSinceEpoch(int(value.timestamp()))
