"""时间解析与排序辅助函数。"""

from __future__ import annotations

import datetime as dt
import re
from typing import Optional, Tuple

from .constants import DEFAULT_TIMEZONE, TIME_GRANULARITY_DAY, TIME_GRANULARITY_EMPTY, TIME_GRANULARITY_MONTH, TIME_GRANULARITY_YEAR


def utc_now_iso() -> str:
    """返回 UTC ISO 时间字符串。"""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_year(value: Optional[str]) -> Optional[int]:
    """从字符串中提取前导年份。"""
    if not value:
        return None
    match = re.match(r"^\s*([+-]?\d{1,6})", str(value))
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def get_sort_bucket(year: Optional[int], month: Optional[int] = None, day: Optional[int] = None) -> int:
    """根据时间精度返回排序粒度。"""
    if year is None:
        return TIME_GRANULARITY_EMPTY
    if month is None:
        return TIME_GRANULARITY_YEAR
    if day is None:
        return TIME_GRANULARITY_MONTH
    return TIME_GRANULARITY_DAY


def to_iso_format(year: int, month: int = 1, day: int = 1) -> str:
    """将年月日转换为 UTC ISO 8601 字符串。"""
    return dt.datetime(year, month, day, tzinfo=dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def from_iso_format(iso_str: str) -> tuple[int, int, int]:
    """从 ISO 8601 字符串解析出年月日。"""
    raw = str(iso_str).strip().replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(raw)
    return parsed.year, parsed.month, parsed.day


def _parse_time_value(value: Optional[str]) -> Tuple[Optional[int], Optional[int], Optional[int], int]:
    """兼容旧接口的时间解析。"""
    if value is None:
        return None, None, None, TIME_GRANULARITY_EMPTY
    normalized = str(value).strip()
    if not normalized:
        return None, None, None, TIME_GRANULARITY_EMPTY

    match = re.fullmatch(r"([+-]?\d{1,6})(?:-(\d{1,2})(?:-(\d{1,2}))?)?", normalized)
    if not match:
        return parse_year(normalized), None, None, TIME_GRANULARITY_DAY

    year = int(match.group(1))
    month_raw = match.group(2)
    day_raw = match.group(3)

    if month_raw is None:
        return year, None, None, TIME_GRANULARITY_YEAR

    month = int(month_raw)
    if month < 1 or month > 12:
        return year, None, None, TIME_GRANULARITY_DAY

    if day_raw is None:
        return year, month, None, TIME_GRANULARITY_MONTH

    day = int(day_raw)
    if day < 1 or day > 31:
        return year, month, None, TIME_GRANULARITY_DAY

    return year, month, day, TIME_GRANULARITY_DAY


def parse_time_components(*args, **kwargs):
    """解析时间。

    兼容两种调用方式：
    - parse_time_components(value): 返回 (year, month, day, sort_bucket)
    - parse_time_components(year, month, day): 返回时间字典
    """
    if len(args) == 1 and not kwargs:
        return _parse_time_value(args[0])

    if kwargs:
        year = kwargs.get("year")
        month = kwargs.get("month")
        day = kwargs.get("day")
    else:
        year = args[0] if len(args) > 0 else None
        month = args[1] if len(args) > 1 else None
        day = args[2] if len(args) > 2 else None

    sort_bucket = get_sort_bucket(year, month, day)
    iso = to_iso_format(year, month, day) if year is not None else None
    return {
        "iso": iso,
        "year": year,
        "month": month,
        "day": day,
        "sort_bucket": sort_bucket,
    }


def to_local_tz(iso_str: str, tz: str = DEFAULT_TIMEZONE) -> str:
    """将 UTC ISO 字符串转换为指定时区的本地时间字符串。"""
    raw = str(iso_str).strip().replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(raw)
    local = parsed.astimezone(dt.timezone(dt.timedelta(hours=8 if tz == DEFAULT_TIMEZONE else 0)))
    return local.isoformat(timespec="seconds")


def from_local_tz(local_str: str, tz: str = DEFAULT_TIMEZONE) -> str:
    """将本地时间字符串转换为 UTC ISO 格式。"""
    parsed = dt.datetime.fromisoformat(str(local_str).strip())
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone(dt.timedelta(hours=8 if tz == DEFAULT_TIMEZONE else 0)))
    return parsed.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def format_date_for_display(iso_str: str, tz: str = DEFAULT_TIMEZONE, with_time: bool = False) -> str:
    """格式化为用户友好的日期字符串。"""
    if not iso_str:
        return ""
    try:
        local = to_local_tz(iso_str, tz=tz)
    except ValueError:
        return str(iso_str)
    if not with_time:
        return local.split("T", 1)[0]
    return local.replace("+08:00", "")


def is_before(iso_str1: str, iso_str2: str) -> bool:
    """比较两个时间的先后顺序。"""
    return dt.datetime.fromisoformat(str(iso_str1).replace("Z", "+00:00")) < dt.datetime.fromisoformat(str(iso_str2).replace("Z", "+00:00"))


def time_range_overlaps(range1: tuple[str, str], range2: tuple[str, str]) -> bool:
    """检查两个时间范围是否重叠。"""
    start1, end1 = (dt.datetime.fromisoformat(item.replace("Z", "+00:00")) for item in range1)
    start2, end2 = (dt.datetime.fromisoformat(item.replace("Z", "+00:00")) for item in range2)
    return max(start1, start2) <= min(end1, end2)
