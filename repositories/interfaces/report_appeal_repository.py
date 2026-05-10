from __future__ import annotations

from abc import ABC, abstractmethod

from models.report_appeal_model import ReportAppeal


class IReportAppealRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[ReportAppeal]:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, report_appeal_id: int) -> ReportAppeal | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_submitter(self, submitter_id: int) -> list[ReportAppeal]:
        raise NotImplementedError

    @abstractmethod
    def list_by_status(self, status: str) -> list[ReportAppeal]:
        raise NotImplementedError

    @abstractmethod
    def save(self, report_appeal: ReportAppeal) -> ReportAppeal:
        raise NotImplementedError

    @abstractmethod
    def update(self, report_appeal: ReportAppeal) -> ReportAppeal:
        raise NotImplementedError
