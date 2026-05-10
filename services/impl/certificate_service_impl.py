from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from config.paths import CERTIFICATES_DIR
from models.certificate_model import Certificate
from repositories.interfaces.activity_repository import IActivityRepository
from repositories.interfaces.certificate_repository import ICertificateRepository
from repositories.interfaces.checkin_repository import ICheckinRepository
from services.interfaces.certificate_service import CertificateDTO, CertificateResult, ICertificateService
from utils.datetime_utils import current_datetime
from utils.permission_checker import PERMISSION_DENIED_MESSAGE, PermissionChecker


class CertificateServiceImpl(ICertificateService):
    def __init__(
        self,
        session: Session,
        activity_repository: IActivityRepository,
        checkin_repository: ICheckinRepository,
        certificate_repository: ICertificateRepository,
    ) -> None:
        self._session = session
        self._activity_repository = activity_repository
        self._checkin_repository = checkin_repository
        self._certificate_repository = certificate_repository

    def generate_certificate(self, current_user, activity_id: int) -> CertificateResult:
        if not PermissionChecker.is_participant(current_user):
            return CertificateResult(False, PERMISSION_DENIED_MESSAGE)

        activity = self._activity_repository.find_by_id(activity_id)
        if activity is None:
            return CertificateResult(False, "活动不存在。")

        checkin = self._checkin_repository.find_by_activity_and_user(activity_id, current_user.id)
        if checkin is None or checkin.status not in {"checked_in", "corrected"}:
            return CertificateResult(False, "只有已签到用户可以生成证书。")

        existing = self._certificate_repository.find_by_user_and_activity(current_user.id, activity_id)
        if existing is not None:
            return CertificateResult(True, "证书已生成，已返回已有证书。", certificate=self._to_dto(existing))

        certificate_no = self._generate_certificate_no()
        file_path = CERTIFICATES_DIR / f"{certificate_no}.pdf"
        self._create_pdf(file_path, current_user, activity, certificate_no)

        certificate = Certificate(
            user_id=current_user.id,
            activity_id=activity_id,
            certificate_no=certificate_no,
            certificate_type="activity_participation",
            file_path=str(file_path),
        )
        self._certificate_repository.save(certificate)
        self._session.commit()
        certificate = self._certificate_repository.find_by_id(certificate.id)
        return CertificateResult(True, "证书生成成功。", certificate=self._to_dto(certificate))

    def list_my_certificates(self, current_user) -> CertificateResult:
        if not PermissionChecker.is_participant(current_user):
            return CertificateResult(False, PERMISSION_DENIED_MESSAGE)
        certificates = self._certificate_repository.list_by_user(current_user.id)
        return CertificateResult(
            True,
            "查询成功。",
            certificates=[self._to_dto(certificate) for certificate in certificates],
        )

    def _create_pdf(self, file_path: Path, current_user, activity, certificate_no: str) -> None:
        CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        pdf = canvas.Canvas(str(file_path), pagesize=A4)
        width, height = A4
        pdf.setFont("STSong-Light", 24)
        pdf.drawCentredString(width / 2, height - 90, "校园活动参与证明")

        pdf.setFont("STSong-Light", 14)
        lines = [
            f"用户姓名：{current_user.name}",
            f"活动名称：{activity.title}",
            f"活动时间：{activity.start_time.strftime('%Y-%m-%d %H:%M')} 至 {activity.end_time.strftime('%Y-%m-%d %H:%M')}",
            f"学分：{activity.credit:g}",
            f"志愿时长：{activity.volunteer_hours:g}",
            f"证书编号：{certificate_no}",
            f"生成时间：{current_datetime().strftime('%Y-%m-%d %H:%M:%S')}",
            "平台名称：校园活动一站式管理平台",
        ]
        y = height - 150
        for line in lines:
            pdf.drawString(110, y, line)
            y -= 34

        pdf.showPage()
        pdf.save()

    def _generate_certificate_no(self) -> str:
        return f"CERT-{current_datetime().strftime('%Y%m%d')}-{uuid4().hex[:10].upper()}"

    def _to_dto(self, certificate: Certificate) -> CertificateDTO:
        return CertificateDTO(
            certificate_id=certificate.id,
            user_id=certificate.user_id,
            activity_id=certificate.activity_id,
            activity_title=certificate.activity.title if certificate.activity else "",
            user_name=certificate.user.name if certificate.user else "",
            certificate_no=certificate.certificate_no,
            certificate_type=certificate.certificate_type,
            file_path=Path(certificate.file_path),
            generated_at=certificate.generated_at,
        )
