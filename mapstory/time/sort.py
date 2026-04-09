"""事件时间排序。"""

from __future__ import annotations

from .model import StructuredTime

TIME_PRECISION_YEAR = 0
TIME_PRECISION_MONTH = 1
TIME_PRECISION_DAY = 2
TIME_PRECISION_HOUR = 3
TIME_PRECISION_MINUTE = 4
TIME_PRECISION_EMPTY = 5


def infer_precision_rank(
    year: int | None,
    month: int | None,
    day: int | None,
    hour: int | None,
    minute: int | None,
) -> int:
    """根据结构化字段推断精度排序权重。"""
    if year is None:
        return TIME_PRECISION_EMPTY
    if month is None:
        return TIME_PRECISION_YEAR
    if day is None:
        return TIME_PRECISION_MONTH
    if hour is None:
        return TIME_PRECISION_DAY
    if minute is None:
        return TIME_PRECISION_HOUR
    return TIME_PRECISION_MINUTE


def build_sort_key(value: StructuredTime | None) -> tuple[int, int, int, int, int, int, int]:
    """构造统一的事件时间排序键。"""
    if value is None or value.year is None:
        return (1, 0, 1, 1, 0, 0, TIME_PRECISION_EMPTY)
    return (
        0,
        value.year,
        value.month or 1,
        value.day or 1,
        value.hour or 0,
        value.minute or 0,
        infer_precision_rank(value.year, value.month, value.day, value.hour, value.minute),
    )
