from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CertificateDTO:
    certificate_id: int
    user_id: int
    activity_id: int
    activity_title: str
    user_name: str
    certificate_no: str
    certificate_type: str
    file_path: Path
    generated_at: datetime


@dataclass(frozen=True)
class CertificateResult:
    success: bool
    message: str
    certificate: CertificateDTO | None = None
    certificates: list[CertificateDTO] | None = None


class ICertificateService(ABC):
    @abstractmethod
    def generate_certificate(self, current_user: Any, activity_id: int) -> CertificateResult:
        raise NotImplementedError

    @abstractmethod
    def list_my_certificates(self, current_user: Any) -> CertificateResult:
        raise NotImplementedError
