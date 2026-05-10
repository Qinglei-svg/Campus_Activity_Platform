from __future__ import annotations

import sys
from pathlib import Path


def _resource_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _runtime_base_dir() -> Path:
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
