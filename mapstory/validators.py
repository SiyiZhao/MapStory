"""输入规范化与校验函数。"""

from __future__ import annotations

import re
from typing import Optional, Sequence, Tuple, Union

from .constants import PRIORITY_CHOICES, PRIORITY_LABELS
from .errors import InputValidationError


def normalize_optional_text(value: Optional[str]) -> Optional[str]:
    """将可选文本去空白并标准化为空值。"""
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def normalize_persons(raw: Optional[Union[str, Sequence[str]]]) -> str:
    """标准化人物列表文本。"""
    if not raw:
        return ""
    if isinstance(raw, (list, tuple, set)):
        parts = [str(p).strip() for p in raw if str(p).strip()]
    else:
        parts = [p.strip() for p in re.split(r"[;,]", str(raw)) if p.strip()]
    return ", ".join(parts)


def validate_priority(priority: Optional[str]) -> Optional[str]:
    """校验并标准化优先级字段。"""
    if priority is None:
        return None
    raw = normalize_optional_text(priority)
    if raw is None:
        return None
    if raw in PRIORITY_CHOICES:
        return PRIORITY_CHOICES[raw]
    if raw in PRIORITY_LABELS:
        return raw
    raise InputValidationError("priority 必须为 fact/doubt/fanon/abridged_fact 或对应中文标签")


def validate_event_text(event: Optional[str]) -> str:
    """校验事件描述为非空文本。"""
    value = normalize_optional_text(event)
    if value is None:
        raise InputValidationError("event 不能为空")
    return value


def validate_coordinates(lat: Optional[float], lon: Optional[float]) -> None:
    """校验经纬度取值范围。"""
    if lat is not None and (lat < -90 or lat > 90):
        raise InputValidationError("lat 超出范围，必须在 -90 到 90 之间")
    if lon is not None and (lon < -180 or lon > 180):
        raise InputValidationError("lon 超出范围，必须在 -180 到 180 之间")


def normalize_numeric_range(
    values: Optional[Sequence[float]],
    *,
    label: str,
    min_value: float,
    max_value: float,
) -> Optional[Tuple[float, float]]:
    """校验并标准化数值区间。"""
    if not values:
        return None
    if len(values) != 2:
        raise InputValidationError(f"{label} 需要两个值")
    start = float(values[0])
    end = float(values[1])
    if start > end:
        start, end = end, start
    if start < min_value or end > max_value:
        raise InputValidationError(f"{label} 超出范围，允许区间为 {min_value} 到 {max_value}")
    return start, end
