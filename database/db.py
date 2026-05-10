from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.paths import DATABASE_FILE, ensure_data_directories


class Base(DeclarativeBase):
    pass


engine = create_engine(
    f"sqlite:///{DATABASE_FILE.as_posix()}",
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def import_all_models() -> None:
    import models.activity_model  # noqa: F401
    import models.activity_result_model  # noqa: F401
    import models.audit_log_model  # noqa: F401
    import models.certificate_model  # noqa: F401
    import models.checkin_model  # noqa: F401
    import models.notification_model  # noqa: F401
    import models.registration_model  # noqa: F401
    import models.report_appeal_model  # noqa: F401
    import models.review_model  # noqa: F401
    import models.role_model  # noqa: F401
    import models.user_model  # noqa: F401


def create_database() -> None:
    ensure_data_directories()
    import_all_models()
    Base.metadata.create_all(bind=engine)
    migrate_database()


def migrate_database() -> None:
    inspector = inspect(engine)
    if "user" not in inspector.get_table_names():
        return
    user_columns = {column["name"] for column in inspector.get_columns("user")}
    with engine.begin() as connection:
        if "frozen_until" not in user_columns:
            connection.execute(text("ALTER TABLE user ADD COLUMN frozen_until DATETIME"))


def initialize_database() -> None:
    from database.init_data import initialize_default_data

    create_database()
    with SessionLocal() as session:
        initialize_default_data(session)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
