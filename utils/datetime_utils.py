from __future__ import annotations

from datetime import datetime, timedelta


def current_datetime() -> datetime:
    return datetime.now()


def add_days(base_time: datetime, days: int, hours: int = 0) -> datetime:
    return base_time + timedelta(days=days, hours=hours)
