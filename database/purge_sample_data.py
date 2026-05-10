from __future__ import annotations

"""清除除快速登录三账号外的业务数据与额外用户，保留角色/分类/权限等基础配置。"""

from sqlalchemy import delete
from sqlalchemy.orm import Session

from database.db import SessionLocal, import_all_models
from database.init_data import QUICK_LOGIN_ACCOUNTS
from models.activity_model import Activity
from models.activity_result_model import ActivityResult
from models.audit_log_model import AuditLog
from models.certificate_model import Certificate
from models.checkin_model import CheckinRecord
from models.notification_model import Notification
from models.registration_model import Registration
from models.report_appeal_model import ReportAppeal
from models.review_model import Review
from models.user_model import PublisherApplication, User


def purge_sample_data(session: Session) -> None:
    import_all_models()
    # 依赖顺序：先子表，再活动；通知/申诉/日志与 user 相关，先清再删用户
    session.execute(delete(CheckinRecord))
    session.execute(delete(Registration))
    session.execute(delete(Review))
    session.execute(delete(Certificate))
    session.execute(delete(ActivityResult))
    session.execute(delete(Activity))
    session.execute(delete(PublisherApplication))
    session.execute(delete(Notification))
    session.execute(delete(ReportAppeal))
    session.execute(delete(AuditLog))
    session.execute(delete(User).where(User.account.not_in(list(QUICK_LOGIN_ACCOUNTS))))


def main() -> None:
    with SessionLocal() as session:
        purge_sample_data(session)
        session.commit()
    print("已清除测试数据，仅保留账号:", ", ".join(sorted(QUICK_LOGIN_ACCOUNTS)))


if __name__ == "__main__":
    main()
