"""事件时间模型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StructuredTime:
    """MapStory 事件时间。"""

    year: int | None
    month: int | None
    day: int | None
    hour: int | None
    minute: int | None
    time_note: str | None = None
