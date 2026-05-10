from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.bootstrap import bootstrap_application
from database.db import initialize_database


def main() -> int:
    initialize_database()
    qt_app = QApplication(sys.argv)
    desktop_app = bootstrap_application(qt_app)
    desktop_app.show()
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
