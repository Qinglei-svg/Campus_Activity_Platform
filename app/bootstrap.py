from __future__ import annotations

from PySide6.QtWidgets import QApplication

from app.application_context import ApplicationContext
from config.paths import ensure_data_directories
from ui.app import CampusActivityDesktopApp


def bootstrap_application(qt_app: QApplication) -> CampusActivityDesktopApp:
    ensure_data_directories()
    context = ApplicationContext()
    return CampusActivityDesktopApp(qt_app=qt_app, context=context)
