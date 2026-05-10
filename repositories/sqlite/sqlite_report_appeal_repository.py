from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.report_appeal_model import ReportAppeal
from models.user_model import User
from repositories.interfaces.report_appeal_repository import IReportAppealRepository


class SQLiteReportAppealRepository(IReportAppealRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[ReportAppeal]:
        statement = (
            select(ReportAppeal)
            .options(
                joinedload(ReportAppeal.submitter).joinedload(User.role),
                joinedload(ReportAppeal.handler).joinedload(User.role),
            )
            .order_by(ReportAppeal.submitted_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def find_by_id(self, report_appeal_id: int) -> ReportAppeal | None:
        statement = (
            select(ReportAppeal)
            .options(
                joinedload(ReportAppeal.submitter).joinedload(User.role),
                joinedload(ReportAppeal.handler).joinedload(User.role),
            )
            .where(ReportAppeal.id == report_appeal_id)
        )
        return self._session.scalar(statement)

    def list_by_submitter(self, submitter_id: int) -> list[ReportAppeal]:
        statement = (
            select(ReportAppeal)
            .options(
                joinedload(ReportAppeal.submitter).joinedload(User.role),
                joinedload(ReportAppeal.handler).joinedload(User.role),
            )
            .where(ReportAppeal.submitter_id == submitter_id)
            .order_by(ReportAppeal.submitted_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def list_by_status(self, status: str) -> list[ReportAppeal]:
        statement = (
            select(ReportAppeal)
            .options(
                joinedload(ReportAppeal.submitter).joinedload(User.role),
                joinedload(ReportAppeal.handler).joinedload(User.role),
            )
            .where(ReportAppeal.status == status)
            .order_by(ReportAppeal.submitted_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def save(self, report_appeal: ReportAppeal) -> ReportAppeal:
        self._session.add(report_appeal)
        self._session.flush()
        return report_appeal

    def update(self, report_appeal: ReportAppeal) -> ReportAppeal:
        merged_report_appeal = self._session.merge(report_appeal)
        self._session.flush()
        return merged_report_appeal
