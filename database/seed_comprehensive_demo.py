"""综合演示数据（幂等，分两批）：初始化时自动写入；各批有独立锚点活动，已存在则跳过该批。

额外演示用户默认密码均为：demo123456（与 admin / publisher / student 三账号无关）。
"""

from __future__ import annotations

import secrets
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config.paths import CERTIFICATES_DIR, ensure_data_directories
from models.activity_model import Activity, ActivityCategory
from models.activity_result_model import ActivityResult
from models.audit_log_model import AuditLog
from models.certificate_model import Certificate
from models.checkin_model import CheckinRecord
from models.notification_model import Notification
from models.registration_model import Registration
from models.report_appeal_model import ReportAppeal
from models.review_model import Review
from models.role_model import Role
from models.user_model import PublisherApplication, User
from utils.datetime_utils import add_days, current_datetime
from utils.password_utils import hash_password

ANCHOR_BATCH1 = "[演示] 人工智能科普讲座"
ANCHOR_BATCH2 = "[演示] 批次二-公开辩论邀请赛"
DEMO_PASSWORD = "demo123456"


def seed_comprehensive_demo_if_needed(
    session: Session,
    roles: dict[str, Role],
    base_users: dict[str, User],
    categories: dict[str, ActivityCategory],
) -> None:
    if not session.scalar(select(Activity.id).where(Activity.title == ANCHOR_BATCH1)):
        _seed_demo_batch_1(session, roles, base_users, categories)
    if not session.scalar(select(Activity.id).where(Activity.title == ANCHOR_BATCH2)):
        _seed_demo_batch_2(session, roles, base_users, categories)


def _seed_demo_batch_1(
    session: Session,
    roles: dict[str, Role],
    base_users: dict[str, User],
    categories: dict[str, ActivityCategory],
) -> None:
    ensure_data_directories()
    pwd = hash_password(DEMO_PASSWORD)
    pub = base_users["publisher"]
    admin = base_users["admin"]

    def add_user(account: str, name: str, role_code: str, phone: str) -> User:
        existing = session.scalar(select(User).where(User.account == account))
        if existing is not None:
            return existing
        u = User(
            role_id=roles[role_code].id,
            account=account,
            name=name,
            password_hash=pwd,
            auth_status="approved",
            status="enabled",
            phone=phone,
            violation_count=0,
        )
        session.add(u)
        session.flush()
        return u

    demo_li = add_user("demo_li", "李四", "participant", "13800001001")
    demo_wang = add_user("demo_wang", "王五", "participant", "13800001002")
    demo_zhao = add_user("demo_zhao", "赵六", "participant", "13800001003")
    demo_qian = add_user("demo_qian", "钱七", "participant", "13800001004")
    demo_pub2 = add_user("demo_pub2", "讲座社李老师", "publisher", "13800001005")

    now = current_datetime()

    def act(
        title: str,
        category_name: str,
        *,
        publisher: User,
        status: str,
        start_off: int,
        end_off_hours: int,
        signup_start_off: int,
        signup_end_off: int,
        capacity: int,
        checkin_code: str,
        checkin_open: bool = False,
        reject_reason: str = "",
        need_audit: bool = False,
        volunteer: float = 0.0,
        credit: float = 1.0,
    ) -> Activity:
        cat = categories[category_name]
        a = Activity(
            publisher_id=publisher.id,
            category_id=cat.id,
            title=title,
            cover_image="",
            description=f"【课程演示数据】{title}。用于展示活动全生命周期与界面效果。",
            start_time=add_days(now, start_off),
            end_time=add_days(now, start_off, hours=end_off_hours),
            signup_start_time=add_days(now, signup_start_off),
            signup_end_time=add_days(now, signup_end_off),
            location="大学生活动中心 301",
            capacity=capacity,
            signup_condition="本校在籍学生",
            need_signup_audit=need_audit,
            credit=credit,
            volunteer_hours=volunteer,
            status=status,
            checkin_code=checkin_code,
            checkin_method="code",
            checkin_open=checkin_open,
            reject_reason=reject_reason,
        )
        session.add(a)
        session.flush()
        return a

    a_ai = act(
        ANCHOR_BATCH1,
        "学术讲座",
        publisher=pub,
        status="online",
        start_off=3,
        end_off_hours=2,
        signup_start_off=-2,
        signup_end_off=2,
        capacity=80,
        checkin_code="DEMOAI01",
        checkin_open=True,
    )
    a_vol = act(
        "[演示] 社区清洁志愿行",
        "志愿公益",
        publisher=pub,
        status="online",
        start_off=10,
        end_off_hours=4,
        signup_start_off=0,
        signup_end_off=9,
        capacity=40,
        checkin_code="DEMOVOL1",
        volunteer=4.0,
        credit=0.5,
    )
    a_sport = act(
        "[演示] 院系羽毛球团体赛",
        "文体赛事",
        publisher=pub,
        status="online",
        start_off=14,
        end_off_hours=5,
        signup_start_off=1,
        signup_end_off=13,
        capacity=32,
        checkin_code="DEMOSPT1",
    )
    a_pending = act(
        "[演示] 社团开放日路演",
        "社团活动",
        publisher=pub,
        status="pending_review",
        start_off=20,
        end_off_hours=6,
        signup_start_off=2,
        signup_end_off=19,
        capacity=150,
        checkin_code="DEMOCLB1",
    )
    act(
        "[演示] 暑期社会实践动员会（草稿）",
        "校级活动",
        publisher=pub,
        status="draft",
        start_off=30,
        end_off_hours=2,
        signup_start_off=5,
        signup_end_off=28,
        capacity=200,
        checkin_code="DEMODRF1",
    )
    a_reject = act(
        "[演示] 已驳回：场地冲突的讲座",
        "学术讲座",
        publisher=pub,
        status="rejected",
        start_off=40,
        end_off_hours=2,
        signup_start_off=-5,
        signup_end_off=35,
        capacity=60,
        checkin_code="DEMORJ1",
        reject_reason="场地审批未通过，请修改地点后重新提交。",
    )
    act(
        "[演示] 已取消：因天气原因延期",
        "文体赛事",
        publisher=pub,
        status="cancelled",
        start_off=-5,
        end_off_hours=3,
        signup_start_off=-20,
        signup_end_off=-6,
        capacity=100,
        checkin_code="DEMOCXL1",
    )
    a_archive = act(
        "[演示] 往届：迎新晚会总结场",
        "校级活动",
        publisher=pub,
        status="archived",
        start_off=-120,
        end_off_hours=3,
        signup_start_off=-140,
        signup_end_off=-121,
        capacity=500,
        checkin_code="DEMOARC1",
        checkin_open=False,
    )
    a_pub2 = act(
        "[演示] 讲座社：四六级备考分享",
        "学术讲座",
        publisher=demo_pub2,
        status="online",
        start_off=7,
        end_off_hours=2,
        signup_start_off=0,
        signup_end_off=6,
        capacity=120,
        checkin_code="DEMOP2X1",
    )

    def reg_code() -> str:
        return f"SEED{secrets.token_hex(10).upper()}"

    def add_reg(activity: Activity, user: User, status: str = "registered", waiting_order: int | None = None) -> Registration:
        r = Registration(
            activity_id=activity.id,
            user_id=user.id,
            status=status,
            waiting_order=waiting_order,
            registration_code=reg_code(),
            registered_at=add_days(now, -1),
            canceled_at=None,
        )
        session.add(r)
        session.flush()
        return r

    r_stu_ai = add_reg(a_ai, base_users["student"])
    r_li_ai = add_reg(a_ai, demo_li)
    add_reg(a_ai, demo_wang)
    add_reg(a_ai, demo_zhao)
    add_reg(a_ai, demo_qian, status="waiting", waiting_order=1)

    add_reg(a_vol, demo_li)
    add_reg(a_vol, demo_wang)

    add_reg(a_sport, base_users["student"])
    add_reg(a_sport, demo_zhao)

    r_stu_arc = add_reg(a_archive, base_users["student"])
    r_li_arc = add_reg(a_archive, demo_li)

    add_reg(a_pub2, demo_zhao)
    add_reg(a_pub2, demo_qian)
    add_reg(a_pub2, base_users["student"])

    def add_checkin(activity: Activity, user: User, registration: Registration | None) -> None:
        session.add(
            CheckinRecord(
                activity_id=activity.id,
                user_id=user.id,
                registration_id=registration.id if registration else None,
                checkin_method="password",
                status="checked_in",
                checkin_time=add_days(now, -1),
                location_info="",
                operator_type="user",
                operator_id=None,
                correction_reason="",
            )
        )

    add_checkin(a_ai, base_users["student"], r_stu_ai)
    add_checkin(a_ai, demo_li, r_li_ai)
    add_checkin(a_archive, base_users["student"], r_stu_arc)
    add_checkin(a_archive, demo_li, r_li_arc)

    def add_review(activity: Activity, user: User, comment: str) -> None:
        session.add(
            Review(
                activity_id=activity.id,
                user_id=user.id,
                content_score=4.5,
                organization_score=4.8,
                experience_score=4.6,
                overall_score=4.6,
                comment=comment,
                status="visible",
            )
        )

    add_review(a_archive, base_users["student"], "现场氛围很好，工作人员负责。")
    add_review(a_archive, demo_li, "流程清晰，希望以后多办。")

    cert_path = CERTIFICATES_DIR / "SEED_DEMO_CERT_ARCHIVE.pdf"
    if not cert_path.exists():
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfgen import canvas

        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        cv = canvas.Canvas(str(cert_path), pagesize=A4)
        cv.setFont("STSong-Light", 14)
        cv.drawString(80, 800, "校园活动参与证明（演示数据）")
        cv.drawString(80, 760, f"活动：{a_archive.title}")
        cv.drawString(80, 720, "证书编号：SEED-DEMO-ARCH-001")
        cv.save()

    session.add(
        Certificate(
            user_id=base_users["student"].id,
            activity_id=a_archive.id,
            certificate_no="SEED-DEMO-ARCH-001",
            certificate_type="activity_participation",
            file_path=str(cert_path),
        )
    )

    session.add(
        ActivityResult(
            activity_id=a_archive.id,
            news_title="迎新晚会圆满落幕",
            summary="本届迎新晚会参与人数超 500 人，现场秩序良好。",
            image_files="",
            attachment_file="",
        )
    )

    session.add(
        PublisherApplication(
            user_id=demo_wang.id,
            organization_name="青年志愿者协会",
            responsible_person="王五",
            contact_info="13800001002",
            proof_file="",
            status="pending",
            reject_reason="",
        )
    )

    session.add(
        ReportAppeal(
            submitter_id=demo_zhao.id,
            target_type="activity",
            target_id=a_vol.id,
            reason="活动内容与宣传不符，请核实。",
            evidence_file="",
            status="pending",
            result="",
        )
    )
    session.add(
        ReportAppeal(
            submitter_id=demo_li.id,
            target_type="activity",
            target_id=a_reject.id,
            reason="该活动已驳回仍出现在历史列表中，建议优化展示。",
            evidence_file="",
            status="ignored",
            result="经核实为正常历史记录，不予处理。",
            handler_id=admin.id,
            handled_at=now,
        )
    )

    session.add(
        Notification(
            receiver_id=admin.id,
            type="activity_review",
            title="有新的活动待审核",
            content=f"发布者【{pub.name}】提交了活动【{a_pending.title}】，请及时审核。",
            is_read=False,
        )
    )
    session.add(
        Notification(
            receiver_id=pub.id,
            type="system",
            title="演示数据已就绪",
            content="数据库已写入一批[演示]前缀的示例活动与用户，便于验收与截图。",
            is_read=True,
            read_at=now,
        )
    )
    session.add(
        Notification(
            receiver_id=base_users["student"].id,
            type="activity",
            title="你报名的活动即将开始",
            content=f"【{a_ai.title}】将于近期举行，请关注签到安排。",
            is_read=False,
        )
    )
    session.add(
        Notification(
            receiver_id=demo_li.id,
            type="activity",
            title="候补提醒（演示）",
            content=f"活动【{a_ai.title}】名额已满，你已处于候补队列。",
            is_read=False,
        )
    )

    session.add(
        AuditLog(
            operator_id=admin.id,
            target_type="activity",
            target_id=a_pending.id,
            action="seed_demo",
            result="inserted",
            reason="综合演示数据初始化（批次一）",
        )
    )

    session.flush()


def _seed_demo_batch_2(
    session: Session,
    roles: dict[str, Role],
    base_users: dict[str, User],
    categories: dict[str, ActivityCategory],
) -> None:
    """第二批：更多测试用户 + 辩论/黑客松等活动与关联数据。"""
    ensure_data_directories()
    pwd = hash_password(DEMO_PASSWORD)
    pub = base_users["publisher"]
    admin = base_users["admin"]
    now = current_datetime()

    def add_user(account: str, name: str, role_code: str, phone: str) -> User:
        existing = session.scalar(select(User).where(User.account == account))
        if existing is not None:
            return existing
        u = User(
            role_id=roles[role_code].id,
            account=account,
            name=name,
            password_hash=pwd,
            auth_status="approved",
            status="enabled",
            phone=phone,
            violation_count=0,
        )
        session.add(u)
        session.flush()
        return u

    demo_sun = add_user("demo_sun", "孙八", "participant", "13800002001")
    demo_zhou = add_user("demo_zhou", "周九", "participant", "13800002002")
    demo_wu = add_user("demo_wu", "吴十", "participant", "13800002003")
    demo_zheng = add_user("demo_zheng", "郑十一", "participant", "13800002004")
    demo_pub3 = add_user("demo_pub3", "体育部张老师", "publisher", "13800002005")

    def act(
        title: str,
        category_name: str,
        *,
        publisher: User,
        status: str,
        start_off: int,
        end_off_hours: int,
        signup_start_off: int,
        signup_end_off: int,
        capacity: int,
        checkin_code: str,
        checkin_open: bool = False,
        volunteer: float = 0.0,
        credit: float = 1.0,
    ) -> Activity:
        cat = categories[category_name]
        a = Activity(
            publisher_id=publisher.id,
            category_id=cat.id,
            title=title,
            cover_image="",
            description=f"【演示批次二】{title}。用于压力测试列表、导出与统计。",
            start_time=add_days(now, start_off),
            end_time=add_days(now, start_off, hours=end_off_hours),
            signup_start_time=add_days(now, signup_start_off),
            signup_end_time=add_days(now, signup_end_off),
            location="东校区体育馆 / 线上会议室",
            capacity=capacity,
            signup_condition="本校学生；辩论赛需提前组队。",
            need_signup_audit=False,
            credit=credit,
            volunteer_hours=volunteer,
            status=status,
            checkin_code=checkin_code,
            checkin_method="code",
            checkin_open=checkin_open,
            reject_reason="",
        )
        session.add(a)
        session.flush()
        return a

    a_debate = act(
        ANCHOR_BATCH2,
        "学术讲座",
        publisher=pub,
        status="online",
        start_off=5,
        end_off_hours=3,
        signup_start_off=-1,
        signup_end_off=4,
        capacity=24,
        checkin_code="DEMODB02",
        checkin_open=True,
    )
    a_hack = act(
        "[演示] 批次二-校园黑客松24小时",
        "校级活动",
        publisher=pub,
        status="online",
        start_off=18,
        end_off_hours=26,
        signup_start_off=0,
        signup_end_off=17,
        capacity=60,
        checkin_code="DEMOHCK2",
        credit=2.0,
    )
    a_pending2 = act(
        "[演示] 批次二-心理健康周开幕式",
        "其他",
        publisher=demo_pub3,
        status="pending_review",
        start_off=25,
        end_off_hours=2,
        signup_start_off=3,
        signup_end_off=24,
        capacity=300,
        checkin_code="DEMOPND2",
    )
    act(
        "[演示] 批次二-书法体验课（草稿）",
        "社团活动",
        publisher=demo_pub3,
        status="draft",
        start_off=40,
        end_off_hours=2,
        signup_start_off=10,
        signup_end_off=38,
        capacity=25,
        checkin_code="DEMODRF2",
    )

    def reg_code() -> str:
        return f"SEED2{secrets.token_hex(10).upper()}"

    def add_reg(activity: Activity, user: User, status: str = "registered", waiting_order: int | None = None) -> Registration:
        r = Registration(
            activity_id=activity.id,
            user_id=user.id,
            status=status,
            waiting_order=waiting_order,
            registration_code=reg_code(),
            registered_at=add_days(now, -1),
            canceled_at=None,
        )
        session.add(r)
        session.flush()
        return r

    stu = base_users["student"]

    r1 = add_reg(a_debate, stu)
    r2 = add_reg(a_debate, demo_sun)
    add_reg(a_debate, demo_zhou)
    add_reg(a_debate, demo_wu)
    add_reg(a_debate, demo_zheng, status="waiting", waiting_order=1)

    add_reg(a_hack, stu)
    add_reg(a_hack, demo_sun)
    add_reg(a_hack, demo_zhou)
    add_reg(a_hack, demo_wu)

    session.add(
        CheckinRecord(
            activity_id=a_debate.id,
            user_id=stu.id,
            registration_id=r1.id,
            checkin_method="password",
            status="checked_in",
            checkin_time=add_days(now, -1),
            location_info="",
            operator_type="user",
            operator_id=None,
            correction_reason="",
        )
    )
    session.add(
        CheckinRecord(
            activity_id=a_debate.id,
            user_id=demo_sun.id,
            registration_id=r2.id,
            checkin_method="password",
            status="checked_in",
            checkin_time=add_days(now, -1),
            location_info="",
            operator_type="user",
            operator_id=None,
            correction_reason="",
        )
    )

    session.add(
        Review(
            activity_id=a_debate.id,
            user_id=demo_zhou.id,
            content_score=4.2,
            organization_score=4.0,
            experience_score=4.3,
            overall_score=4.2,
            comment="辩题有深度，希望增加观众提问环节。",
            status="visible",
        )
    )

    session.add(
        ReportAppeal(
            submitter_id=demo_wu.id,
            target_type="activity",
            target_id=a_hack.id,
            reason="活动时间过长，建议明确休息区安排。",
            evidence_file="",
            status="pending",
            result="",
        )
    )

    session.add(
        PublisherApplication(
            user_id=demo_sun.id,
            organization_name="思辨社",
            responsible_person="孙八",
            contact_info="13800002001",
            proof_file="",
            status="pending",
            reject_reason="",
        )
    )

    session.add(
        Notification(
            receiver_id=admin.id,
            type="activity_review",
            title="【批次二】待审核活动",
            content=f"发布者【{demo_pub3.name}】提交了【{a_pending2.title}】。",
            is_read=False,
        )
    )
    session.add(
        Notification(
            receiver_id=demo_pub3.id,
            type="system",
            title="演示批次二数据已生成",
            content="已为您创建待审核活动与草稿活动，可用于测试发布者流程。",
            is_read=False,
        )
    )
    session.add(
        Notification(
            receiver_id=demo_sun.id,
            type="activity",
            title="报名成功提醒",
            content=f"你已报名【{a_debate.title}】。",
            is_read=True,
            read_at=now,
        )
    )

    session.add(
        AuditLog(
            operator_id=admin.id,
            target_type="activity",
            target_id=a_debate.id,
            action="seed_demo_batch2",
            result="inserted",
            reason="综合演示数据初始化（批次二）",
        )
    )

    session.flush()


def main() -> None:
    """手动执行：python -m database.seed_comprehensive_demo。"""
    from database.db import initialize_database

    initialize_database()
    print("已完成：建库 + 默认数据 + 综合演示数据（批次一/二按锚点分别幂等）。")


if __name__ == "__main__":
    main()
