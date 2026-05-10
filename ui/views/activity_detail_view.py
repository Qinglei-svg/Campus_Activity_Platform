from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from controllers.activity_controller import ActivityController
from controllers.checkin_controller import CheckinController
from controllers.certificate_controller import CertificateController
from controllers.registration_controller import RegistrationController
from controllers.report_appeal_controller import ReportAppealController
from controllers.review_controller import ReviewController
from services.interfaces.activity_service import ActivityDTO
from services.interfaces.auth_service import AuthenticatedUser
from utils.permission_checker import PermissionChecker
from ui.views.review_submit_dialog import ReviewSubmitDialog
from ui.views.report_submit_dialog import ReportSubmitDialog


class ActivityDetailView(QWidget):
    back_requested = Signal()

    def __init__(
        self,
        activity_id: int,
        current_user: AuthenticatedUser,
        activity_controller: ActivityController,
        registration_controller: RegistrationController | None = None,
        checkin_controller: CheckinController | None = None,
        review_controller: ReviewController | None = None,
        certificate_controller: CertificateController | None = None,
        report_appeal_controller: ReportAppealController | None = None,
        back_button_text: str = "返回活动大厅",
    ) -> None:
        super().__init__()
        self._activity_id = activity_id
        self._current_user = current_user
        self._activity_controller = activity_controller
        self._registration_controller = registration_controller
        self._checkin_controller = checkin_controller
        self._review_controller = review_controller
        self._certificate_controller = certificate_controller
        self._report_appeal_controller = report_appeal_controller
        self._back_button_text = back_button_text

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(14)
        self._load_detail()

    def _load_detail(self) -> None:
        self._clear_layout()
        result = self._activity_controller.get_activity_detail(self._activity_id, self._current_user)
        if not result.success or result.activity is None:
            QMessageBox.warning(self, "查询失败", result.message)
            self.back_requested.emit()
            return
        self._render_detail(result.activity)

    def _render_detail(self, activity: ActivityDTO) -> None:
        title = QLabel(activity.title)
        title.setObjectName("pageTitle")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content = QWidget()
        form = QFormLayout(content)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(18)

        form.addRow("活动分类：", QLabel(activity.category_name))
        form.addRow("主办方：", QLabel(activity.publisher_name))
        form.addRow("活动状态：", QLabel(activity.status))
        form.addRow("活动开始时间：", QLabel(activity.start_time.strftime("%Y-%m-%d %H:%M")))
        form.addRow("活动结束时间：", QLabel(activity.end_time.strftime("%Y-%m-%d %H:%M")))
        form.addRow("报名开始时间：", QLabel(activity.signup_start_time.strftime("%Y-%m-%d %H:%M")))
        form.addRow("报名结束时间：", QLabel(activity.signup_end_time.strftime("%Y-%m-%d %H:%M")))
        form.addRow("活动地点：", QLabel(activity.location))
        form.addRow("人数上限：", QLabel(str(activity.capacity)))
        form.addRow("已报名人数：", QLabel(str(activity.registered_count)))
        form.addRow("剩余名额：", QLabel(str(activity.remaining_count)))
        form.addRow("学分：", QLabel(f"{activity.credit:g}"))
        form.addRow("志愿时长：", QLabel(f"{activity.volunteer_hours:g}"))

        description_label = QLabel(activity.description)
        description_label.setWordWrap(True)
        form.addRow("活动详情描述：", description_label)

        scroll_area.setWidget(content)

        signup_button = QPushButton("立即报名")
        signup_button.setObjectName("primaryButton")
        signup_button.setEnabled(
            PermissionChecker.is_participant(self._current_user)
            and activity.status == "online"
            and self._registration_controller is not None
        )
        signup_button.clicked.connect(lambda: self._register_activity(activity.activity_id))

        checkin_button = QPushButton("输入口令签到")
        checkin_button.setEnabled(
            PermissionChecker.is_participant(self._current_user)
            and activity.status == "online"
            and self._checkin_controller is not None
        )
        checkin_button.clicked.connect(lambda: self._checkin_activity(activity.activity_id))

        review_button = QPushButton("提交评价")
        review_button.setEnabled(
            PermissionChecker.is_participant(self._current_user)
            and activity.status == "online"
            and self._review_controller is not None
        )
        review_button.clicked.connect(lambda: self._open_review_dialog(activity.activity_id))

        certificate_button = QPushButton("生成证书")
        certificate_button.setEnabled(
            PermissionChecker.is_participant(self._current_user)
            and activity.status == "online"
            and self._certificate_controller is not None
        )
        certificate_button.clicked.connect(lambda: self._generate_certificate(activity.activity_id))

        report_activity_button = QPushButton("举报活动")
        report_activity_button.setEnabled(
            PermissionChecker.is_participant(self._current_user)
            and activity.status == "online"
            and self._report_appeal_controller is not None
        )
        report_activity_button.clicked.connect(lambda: self._report_activity(activity))

        report_publisher_button = QPushButton("举报发布者")
        report_publisher_button.setEnabled(
            PermissionChecker.is_participant(self._current_user)
            and activity.status == "online"
            and self._report_appeal_controller is not None
        )
        report_publisher_button.clicked.connect(lambda: self._report_publisher(activity))

        back_button = QPushButton(self._back_button_text)
        back_button.clicked.connect(self.back_requested.emit)

        self._layout.addWidget(title)
        self._layout.addWidget(scroll_area, 1)
        self._layout.addWidget(signup_button)
        self._layout.addWidget(checkin_button)
        self._layout.addWidget(review_button)
        self._layout.addWidget(certificate_button)
        self._layout.addWidget(report_activity_button)
        self._layout.addWidget(report_publisher_button)
        self._layout.addWidget(back_button)

    def _register_activity(self, activity_id: int) -> None:
        if self._registration_controller is None:
            QMessageBox.warning(self, "报名失败", "报名功能暂不可用。")
            return
        result = self._registration_controller.register_activity(activity_id)
        if not result.success:
            QMessageBox.warning(self, "报名失败", result.message)
            return
        QMessageBox.information(self, "报名结果", result.message)
        self._load_detail()

    def _checkin_activity(self, activity_id: int) -> None:
        if self._checkin_controller is None:
            QMessageBox.warning(self, "签到失败", "签到功能暂不可用。")
            return
        code, ok = QInputDialog.getText(self, "活动签到", "请输入签到口令：")
        if not ok:
            return
        result = self._checkin_controller.participant_checkin(activity_id, code)
        if not result.success:
            QMessageBox.warning(self, "签到失败", result.message)
            return
        QMessageBox.information(self, "签到成功", result.message)

    def _open_review_dialog(self, activity_id: int) -> None:
        if self._review_controller is None:
            QMessageBox.warning(self, "评价失败", "评价功能暂不可用。")
            return
        dialog = ReviewSubmitDialog(activity_id, self._review_controller)
        dialog.exec()

    def _generate_certificate(self, activity_id: int) -> None:
        if self._certificate_controller is None:
            QMessageBox.warning(self, "生成失败", "证书功能暂不可用。")
            return
        result = self._certificate_controller.generate_certificate(activity_id)
        if not result.success:
            QMessageBox.warning(self, "生成失败", result.message)
            return
        QMessageBox.information(self, "生成成功", f"{result.message}\n文件路径：{result.certificate.file_path}")

    def _report_activity(self, activity: ActivityDTO) -> None:
        if self._report_appeal_controller is None:
            QMessageBox.warning(self, "提交失败", "举报功能暂不可用。")
            return
        dialog = ReportSubmitDialog(
            "举报活动",
            f"举报活动：{activity.title}",
            lambda reason: self._report_appeal_controller.submit_activity_report(activity.activity_id, reason),
        )
        dialog.exec()

    def _report_publisher(self, activity: ActivityDTO) -> None:
        if self._report_appeal_controller is None:
            QMessageBox.warning(self, "提交失败", "举报功能暂不可用。")
            return
        dialog = ReportSubmitDialog(
            "举报发布者",
            f"举报发布者：{activity.publisher_name}",
            lambda reason: self._report_appeal_controller.submit_publisher_report(activity.publisher_id, reason),
        )
        dialog.exec()

    def _clear_layout(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
