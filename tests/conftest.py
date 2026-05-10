from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

# 必须在任何测试文件 import database / config.paths 之前设置，避免 pytest 污染开发库。
_test_data_root = tempfile.mkdtemp(prefix="campus_activity_pytest_")
os.environ["CAMPUS_ACTIVITY_TEST_DATA_DIR"] = str(Path(_test_data_root).resolve())


def pytest_sessionfinish(session, exitstatus) -> None:
    shutil.rmtree(_test_data_root, ignore_errors=True)
