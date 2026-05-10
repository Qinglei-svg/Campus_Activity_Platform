from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QMessageBox, QVBoxLayout, QWidget

from config.settings import APP_NAME, MAIN_WINDOW_HEIGHT, MAIN_WINDOW_WIDTH
from controllers.activity_controller import ActivityController
from controllers.admin_controller import AdminController
from controllers.audit_log_controller import AuditLogController
from controllers.category_controller import CategoryController
from controllers.checkin_controller import CheckinController
from controllers.certificate_controller import CertificateController
from controllers.export_controller import ExportController
from controllers.notification_controller import NotificationController
from controllers.registration_controller import RegistrationController
from controllers.report_appeal_controller import ReportAppealController
from controllers.review_controller import ReviewController
from controllers.statistics_controller import StatisticsController
from controllers.user_controller import UserController
from services.interfaces.auth_service import AuthenticatedUser
from utils.permission_checker import PermissionChecker
from ui.views.admin_activity_audit_view import AdminActivityAuditView
from ui.views.admin_audit_log_view import AdminAuditLogView
from ui.views.admin_category_manage_view import AdminCategoryManageView
from ui.views.admin_publisher_audit_view import AdminPublisherAuditView
from ui.views.admin_report_appeal_manage_view import AdminReportAppealManageView
from ui.views.admin_statistics_view import AdminStatisticsView
from ui.views.admin_review_manage_view import AdminReviewManageView
from ui.views.admin_user_manage_view import AdminUserManageView
from ui.views.activity_detail_view import ActivityDetailView
from ui.views.activity_hall_view import ActivityHallView
from ui.views.my_registration_view import MyRegistrationView
from ui.views.my_certificate_view import MyCertificateView
from ui.views.notification_view import NotificationView
from ui.views.participant_report_view import ParticipantReportView
from ui.views.participant_center_view import ParticipantCenterView
from ui.views.placeholder_view import PlaceholderView
from ui.views.publisher_activity_create_view import PublisherActivityCreateView
from ui.views.publisher_activity_manage_view import PublisherActivityManageView
from ui.views.publisher_apply_view import PublisherApplyView
from ui.views.publisher_checkin_manage_view import PublisherCheckinManageView
from ui.views.publisher_registration_manage_view import PublisherRegistrationManageView
from ui.views.publisher_review_view import PublisherReviewView
from ui.widgets.sidebar import Sidebar
from ui.widgets.topbar import TopBar


class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(
        self,
        user: AuthenticatedUser,
        notification_controller: NotificationController,
        activity_controller: ActivityController,
        admin_controller: AdminController,
        audit_log_controller: AuditLogController,
        registration_controller: RegistrationController,
        report_appeal_controller: ReportAppealController,
        export_controller: ExportController,
        category_controller: CategoryController,
        checkin_controller: CheckinController,
        review_controller: ReviewController,
        statistics_controller: StatisticsController,
        certificate_controller: CertificateController,
        user_controller: UserController,
    ) -> None:
        super().__init__()
        self._user = user
        self._notification_controller = notification_controller
        self._activity_controller = activity_controller
        self._admin_controller = admin_controller
        self._audit_log_controller = audit_log_controller
        self._registration_controller = registration_controller
        self._report_appeal_controller = report_appeal_controller
        self._export_controller = export_controller
        self._category_controller = category_controller
        self._checkin_controller = checkin_controller
        self._review_controller = review_controller
        self._statistics_controller = statistics_controller
        self._certificate_controller = certificate_controller
        self._user_controller = user_controller
        self.setWindowTitle(APP_NAME)
        self.resize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)
        menus = PermissionChecker.get_allowed_menus(user)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._sidebar = Sidebar(menus)
        self._sidebar.menu_selected.connect(self._handle_menu_selected)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._topbar = TopBar(user_name=user.name, role_name=user.role_name)
        self._topbar.logout_requested.connect(self.logout_requested.emit)

        self._content_container = QWidget()
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(28, 28, 28, 28)

        right_layout.addWidget(self._topbar)
        right_layout.addWidget(self._content_container, 1)

        root_layout.addWidget(self._sidebar)
        root_layout.addWidget(right_panel, 1)

        self.setCentralWidget(root)

        if menus:
            self._show_page(menus[0])

    def _handle_menu_selected(self, page_name: str) -> None:
        permission_result = PermissionChecker.can_access_menu(self._user, page_name)
        if not permission_result.success:
            QMessageBox.warning(self, "权限不足", permission_result.message)
            return
        self._show_page(page_name)

    def _show_page(self, page_name: str) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if page_name == "通知中心":
            self._content_layout.addWidget(NotificationView(self._user, self._notification_controller))
        elif page_name == "活动大厅":
            self._show_activity_hall()
        elif page_name == "创建活动":
            self._show_publisher_activity_create()
        elif page_name == "我的活动":
            self._show_publisher_activity_manage()
        elif page_name == "活动审核":
            self._show_admin_activity_audit()
        elif page_name == "活动分类":
            self._content_layout.addWidget(AdminCategoryManageView(self._category_controller))
        elif page_name == "数据统计":
            self._content_layout.addWidget(AdminStatisticsView(self._statistics_controller))
        elif page_name == "我的报名":
            self._content_layout.addWidget(MyRegistrationView(self._registration_controller))
        elif page_name == "报名管理":
            self._content_layout.addWidget(
                PublisherRegistrationManageView(
                    self._activity_controller,
                    self._export_controller,
                    self._registration_controller,
                    self._report_appeal_controller,
                )
            )
        elif page_name == "签到管理":
            self._content_layout.addWidget(
                PublisherCheckinManageView(self._activity_controller, self._checkin_controller)
            )
        elif page_name == "活动评价":
            self._content_layout.addWidget(
                PublisherReviewView(self._activity_controller, self._review_controller)
            )
        elif page_name == "我的签到":
            self._content_layout.addWidget(ParticipantCenterView(self._checkin_controller, self._statistics_controller))
        elif page_name == "我的证书":
            self._content_layout.addWidget(MyCertificateView(self._certificate_controller))
        elif page_name == "举报申诉处理":
            self._content_layout.addWidget(AdminReportAppealManageView(self._report_appeal_controller))
        elif page_name == "操作日志":
            self._content_layout.addWidget(AdminAuditLogView(self._audit_log_controller))
        elif page_name == "举报申诉":
            self._content_layout.addWidget(ParticipantReportView(self._report_appeal_controller))
        elif page_name == "申请发布者":
            self._content_layout.addWidget(PublisherApplyView(self._user_controller))
        elif page_name == "用户管理":
            self._content_layout.addWidget(AdminUserManageView(self._user_controller))
        elif page_name == "发布者审核":
            self._content_layout.addWidget(AdminPublisherAuditView(self._user_controller))
        else:
            self._content_layout.addWidget(PlaceholderView(page_name))

    def _show_activity_hall(self) -> None:
        hall_view = ActivityHallView(self._activity_controller)
        hall_view.detail_requested.connect(self._show_activity_detail)
        self._content_layout.addWidget(hall_view)

    def _show_activity_detail(self, activity_id: int) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        detail_view = ActivityDetailView(
            activity_id=activity_id,
            current_user=self._user,
            activity_controller=self._activity_controller,
            registration_controller=self._registration_controller,
            checkin_controller=self._checkin_controller,
            review_controller=self._review_controller,
            certificate_controller=self._certificate_controller,
            report_appeal_controller=self._report_appeal_controller,
        )
        detail_view.back_requested.connect(lambda: self._show_page("活动大厅"))
        self._content_layout.addWidget(detail_view)

    def _show_publisher_activity_create(self, activity_id: int | None = None) -> None:
        activity = None
        if activity_id is not None:
            result = self._activity_controller.get_my_activity_detail(activity_id)
            if not result.success or result.activity is None:
                QMessageBox.warning(self, "查询失败", result.message)
                return
            activity = result.activity

        create_view = PublisherActivityCreateView(self._activity_controller, activity=activity)
        create_view.submitted.connect(lambda: self._show_page("我的活动"))
        self._content_layout.addWidget(create_view)

    def _show_publisher_activity_manage(self) -> None:
        manage_view = PublisherActivityManageView(self._activity_controller, self._statistics_controller)
        manage_view.detail_requested.connect(self._show_publisher_activity_detail)
        manage_view.edit_requested.connect(self._show_publisher_activity_edit)
        self._content_layout.addWidget(manage_view)

    def _show_publisher_activity_edit(self, activity_id: int) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._show_publisher_activity_create(activity_id=activity_id)

    def _show_publisher_activity_detail(self, activity_id: int) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        detail_view = ActivityDetailView(
            activity_id=activity_id,
            current_user=self._user,
            activity_controller=self._activity_controller,
            report_appeal_controller=self._report_appeal_controller,
            back_button_text="返回我的活动",
        )
        detail_view.back_requested.connect(lambda: self._show_page("我的活动"))
        self._content_layout.addWidget(detail_view)

    def _show_admin_activity_audit(self) -> None:
        audit_view = AdminActivityAuditView(self._admin_controller)
        audit_view.detail_requested.connect(self._show_admin_activity_detail)
        self._content_layout.addWidget(audit_view)

    def _show_admin_activity_detail(self, activity_id: int) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        detail_view = ActivityDetailView(
            activity_id=activity_id,
            current_user=self._user,
            activity_controller=self._activity_controller,
            report_appeal_controller=self._report_appeal_controller,
            back_button_text="返回活动审核",
        )
        detail_view.back_requested.connect(lambda: self._show_page("活动审核"))
        self._content_layout.addWidget(detail_view)
