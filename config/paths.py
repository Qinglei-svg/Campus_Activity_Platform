from __future__ import annotations

import os
import sys
from pathlib import Path

# 由 tests/conftest 在 import 本模块前设置，使 pytest 不污染开发用 data/ 目录
_TEST_DATA_DIR_ENV = "CAMPUS_ACTIVITY_TEST_DATA_DIR"


def _resource_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _runtime_base_dir() -> Path:
    test_root = os.environ.get(_TEST_DATA_DIR_ENV)
    if test_root:
        return Path(test_root)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _resource_base_dir()
RUNTIME_DIR = _runtime_base_dir()
DATA_DIR = RUNTIME_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
EXPORTS_DIR = DATA_DIR / "exports"
CERTIFICATES_DIR = DATA_DIR / "certificates"
DATABASE_FILE = DATA_DIR / "campus_activity.db"
STYLE_FILE = BASE_DIR / "ui" / "styles" / "style.qss"


def ensure_data_directories() -> None:
    for directory in (DATA_DIR, UPLOADS_DIR, EXPORTS_DIR, CERTIFICATES_DIR):
        directory.mkdir(parents=True, exist_ok=True)
