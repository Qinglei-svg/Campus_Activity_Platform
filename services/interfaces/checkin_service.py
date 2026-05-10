from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CheckinRecordDTO:
    checkin_id: int | None
    activity_id: int
    activity_title: str
    user_id: int
    user_account: str
    user_name: str
    registration_id: int | None
    registration_status: str
    checkin_method: str
    status: str
    checkin_time: datetime | None
    location_info: str
    correction_reason: str


@dataclass(frozen=True)
class CheckinResult:
    success: bool
    message: str
    checkin: CheckinRecordDTO | None = None
    checkins: list[CheckinRecordDTO] | None = None
    qr_code_path: Path | None = None


class ICheckinService(ABC):
    @abstractmethod
    def enable_checkin(self, current_user: Any, activity_id: int, method: str, code: str) -> CheckinResult:
        raise NotImplementedError

    @abstractmethod
    def participant_checkin(self, current_user: Any, activity_id: int, code: str) -> CheckinResult:
        raise NotImplementedError

    @abstractmethod
    def list_activity_checkins(self, current_user: Any, activity_id: int) -> CheckinResult:
        raise NotImplementedError

    @abstractmethod
    def list_my_checkins(self, current_user: Any) -> CheckinResult:
        raise NotImplementedError

    @abstractmethod
    def correct_checkin(self, current_user: Any, registration_id: int, status: str, reason: str) -> CheckinResult:
        raise NotImplementedError
