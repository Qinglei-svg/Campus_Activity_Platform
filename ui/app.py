from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from app.application_context import ApplicationContext
from config.paths import STYLE_FILE
from controllers.activity_controller import ActivityController
from controllers.admin_controller import AdminController
from controllers.audit_log_controller import AuditLogController
from controllers.auth_controller import AuthController
from controllers.checkin_controller import CheckinController
from controllers.certificate_controller import CertificateController
from controllers.export_controller import ExportController
from controllers.category_controller import CategoryController
from controllers.notification_controller import NotificationController
from controllers.registration_controller import RegistrationController
from controllers.report_appeal_controller import ReportAppealController
from controllers.review_controller import ReviewController
from controllers.statistics_controller import StatisticsController
from controllers.user_controller import UserController
from services.interfaces.auth_service import AuthenticatedUser
from ui.views.login_view import LoginView
from ui.views.main_window import MainWindow
from ui.views.register_view import RegisterView


class CampusActivityDesktopApp(QObject):
    def __init__(self, qt_app: QApplication, context: ApplicationContext) -> None:
        super().__init__()
        self._qt_app = qt_app
        self._context = context
        self._auth_controller = AuthController()
        self._notification_controller = NotificationController()
        self._activity_controller = ActivityController(context=self._context)
        self._admin_controller = AdminController(context=self._context)
        self._audit_log_controller = AuditLogController(context=self._context)
        self._registration_controller = RegistrationController(context=self._context)
        self._report_appeal_controller = ReportAppealController(context=self._context)
        self._export_controller = ExportController(context=self._context)
        self._category_controller = CategoryController(context=self._context)
        self._checkin_controller = CheckinController(context=self._context)
        self._review_controller = ReviewController(context=self._context)
        self._statistics_controller = StatisticsController(context=self._context)
        self._certificate_controller = CertificateController(context=self._context)
        self._user_controller = UserController(context=self._context)
        self._login_view = LoginView(self._auth_controller)
        self._register_view = RegisterView(self._auth_controller)
        self._main_window: MainWindow | None = None

        self._load_style_sheet()
        self._bind_events()

    def show(self) -> None:
        self._login_view.show()

    def _load_style_sheet(self) -> None:
        if STYLE_FILE.exists():
            self._qt_app.setStyleSheet(STYLE_FILE.read_text(encoding="utf-8"))

    def _bind_events(self) -> None:
        self._login_view.login_succeeded.connect(self._handle_login_success)
        self._login_view.register_requested.connect(self._show_register_view)
        self._register_view.back_to_login_requested.connect(self._show_login_view)

    def _handle_login_success(self, user: AuthenticatedUser) -> None:
        self._context.set_current_user(user)
        self._login_view.hide()

        self._main_window = MainWindow(
            user=user,
            notification_controller=self._notification_controller,
            activity_controller=self._activity_controller,
            admin_controller=self._admin_controller,
            audit_log_controller=self._audit_log_controller,
            registration_controller=self._registration_controller,
            report_appeal_controller=self._report_appeal_controller,
            export_controller=self._export_controller,
            category_controller=self._category_controller,
            checkin_controller=self._checkin_controller,
            review_controller=self._review_controller,
            statistics_controller=self._statistics_controller,
            certificate_controller=self._certificate_controller,
            user_controller=self._user_controller,
        )
        self._main_window.logout_requested.connect(self._handle_logout)
        self._main_window.show()

    def _show_register_view(self) -> None:
        self._login_view.hide()
        self._register_view.show()

    def _show_login_view(self) -> None:
        self._register_view.hide()
        self._login_view.show()

    def _handle_logout(self) -> None:
        if self._main_window is not None:
            self._main_window.close()
            self._main_window = None

        self._auth_controller.logout()
        self._context.clear_current_user()
        self._login_view.reset_form()
        self._login_view.show()
