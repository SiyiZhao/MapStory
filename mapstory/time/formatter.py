"""事件时间格式化。"""

from __future__ import annotations

from .model import StructuredTime


def format_structured_time(value: StructuredTime | None) -> str:
    """把结构化时间格式化为标准字符串。"""
    if value is None or value.year is None:
        return ""
    if value.month is None:
        return f"{value.year}"
    if value.day is None:
        return f"{value.year}-{value.month:02d}"
    if value.hour is None:
        return f"{value.year}-{value.month:02d}-{value.day:02d}"
    if value.minute is None:
        return f"{value.year}-{value.month:02d}-{value.day:02d} {value.hour:02d}"
    return f"{value.year}-{value.month:02d}-{value.day:02d} {value.hour:02d}:{value.minute:02d}"
