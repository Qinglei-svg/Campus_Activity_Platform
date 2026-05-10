from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ReportAppealDTO:
    report_id: int
    submitter_id: int
    submitter_account: str
    submitter_name: str
    submitter_role_name: str
    target_type: str
    target_id: int
    target_name: str
    target_user_id: int | None
    reason: str
    evidence_file: str
    status: str
    result: str
    handler_name: str
    submitted_at: datetime
    handled_at: datetime | None


@dataclass(frozen=True)
class ReportAppealResult:
    success: bool
    message: str
    report: ReportAppealDTO | None = None
    reports: list[ReportAppealDTO] | None = None


class IReportAppealService(ABC):
    @abstractmethod
    def submit_activity_report(self, current_user: Any, activity_id: int, reason: str) -> ReportAppealResult:
        raise NotImplementedError

    @abstractmethod
    def submit_publisher_report(self, current_user: Any, publisher_id: int, reason: str) -> ReportAppealResult:
        raise NotImplementedError

    @abstractmethod
    def submit_participant_report(self, current_user: Any, participant_id: int, reason: str) -> ReportAppealResult:
        raise NotImplementedError

    @abstractmethod
    def list_my_reports(self, current_user: Any) -> ReportAppealResult:
        raise NotImplementedError

    @abstractmethod
    def list_reports(self, admin_user: Any, status: str | None = None) -> ReportAppealResult:
        raise NotImplementedError

    @abstractmethod
    def punish_report(self, admin_user: Any, report_id: int) -> ReportAppealResult:
        raise NotImplementedError

    @abstractmethod
    def ignore_report(self, admin_user: Any, report_id: int, result: str) -> ReportAppealResult:
        raise NotImplementedError
