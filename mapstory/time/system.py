"""系统时间与时区工具。"""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo


def utc_now_iso() -> str:
    """返回 UTC ISO 时间字符串。"""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def to_local_display(iso_str: str, tz: str = "Asia/Shanghai", *, with_time: bool = True) -> str:
    """把 UTC ISO 字符串转换为本地展示字符串。"""
    parsed = dt.datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
    local = parsed.astimezone(ZoneInfo(tz))
    if with_time:
        return local.isoformat(timespec="seconds")
    return local.date().isoformat()
