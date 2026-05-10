from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExportResult:
    success: bool
    message: str
    file_path: Path | None = None


class IExportService(ABC):
    @abstractmethod
    def export_activity_registration_excel(self, current_user: Any, activity_id: int) -> ExportResult:
        raise NotImplementedError
