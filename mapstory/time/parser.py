"""事件时间解析与校验。"""

from __future__ import annotations

import re

from ..errors import InputValidationError
from .model import StructuredTime

_YEAR_RE = re.compile(r"^([+-]?\d{1,6})$")
_MONTH_RE = re.compile(r"^([+-]?\d{1,6})-(\d{2})$")
_DAY_RE = re.compile(r"^([+-]?\d{1,6})-(\d{2})-(\d{2})$")
_HOUR_RE = re.compile(r"^([+-]?\d{1,6})-(\d{2})-(\d{2}) (\d{2})$")
_MINUTE_RE = re.compile(r"^([+-]?\d{1,6})-(\d{2})-(\d{2}) (\d{2}):(\d{2})$")


def structured_time_from_parts(
    *,
    year: int | None,
    month: int | None,
    day: int | None,
    hour: int | None,
    minute: int | None,
    time_note: str | None = None,
) -> StructuredTime:
    """从拆分字段构造结构化时间。"""
    validate_structured_parts(year=year, month=month, day=day, hour=hour, minute=minute)
    return StructuredTime(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        time_note=time_note,
    )


def parse_time(text: str | None, *, time_note: str | None = None) -> StructuredTime:
    """把输入文本解析为结构化时间。"""
    normalized = (text or "").strip()
    if not normalized:
        return StructuredTime(year=None, month=None, day=None, hour=None, minute=None, time_note=time_note)

    for pattern, group_count in (
        (_MINUTE_RE, 5),
        (_HOUR_RE, 4),
        (_DAY_RE, 3),
        (_MONTH_RE, 2),
        (_YEAR_RE, 1),
    ):
        match = pattern.fullmatch(normalized)
        if not match:
            continue
        parts = [int(match.group(i)) for i in range(1, group_count + 1)]
        while len(parts) < 5:
            parts.append(None)
        year, month, day, hour, minute = parts
        validate_structured_parts(year=year, month=month, day=day, hour=hour, minute=minute)
        return StructuredTime(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            time_note=time_note,
        )

    raise InputValidationError("time 仅支持 YYYY、YYYY-MM、YYYY-MM-DD、YYYY-MM-DD HH、YYYY-MM-DD HH:MM")


def validate_time(text: str | None) -> None:
    """校验时间文本。"""
    parse_time(text)


def validate_structured_parts(
    *,
    year: int | None,
    month: int | None,
    day: int | None,
    hour: int | None,
    minute: int | None,
) -> None:
    """校验结构化时间字段。"""
    if year is None:
        if any(part is not None for part in (month, day, hour, minute)):
            raise InputValidationError("缺少 year 时，month/day/hour/minute 必须为空")
        return
    if month is None:
        if any(part is not None for part in (day, hour, minute)):
            raise InputValidationError("缺少 month 时，day/hour/minute 必须为空")
        return
    if month < 1 or month > 12:
        raise InputValidationError("month 超出范围，必须在 1 到 12 之间")
    if day is None:
        if any(part is not None for part in (hour, minute)):
            raise InputValidationError("缺少 day 时，hour/minute 必须为空")
        return
    if day < 1 or day > _days_in_month(year, month):
        raise InputValidationError("day 超出范围")
    if hour is None:
        if minute is not None:
            raise InputValidationError("缺少 hour 时，minute 必须为空")
        return
    if hour < 0 or hour > 23:
        raise InputValidationError("hour 超出范围，必须在 0 到 23 之间")
    if minute is None:
        return
    if minute < 0 or minute > 59:
        raise InputValidationError("minute 超出范围，必须在 0 到 59 之间")


def _days_in_month(year: int, month: int) -> int:
    """返回指定年月的天数，按公历规则处理。"""
    if month == 2:
        return 29 if _is_leap_year(year) else 28
    if month in {4, 6, 9, 11}:
        return 30
    return 31


def _is_leap_year(year: int) -> bool:
    """判断闰年。"""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
