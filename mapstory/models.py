"""MapStory 数据模型。"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(slots=True)
class TimeInfo:
    """事件时间信息。"""

    iso: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    sort_bucket: int = 3
    t_note: Optional[str] = None


@dataclass(slots=True)
class Location:
    """事件地点信息。"""

    lat: Optional[float] = None
    lon: Optional[float] = None
    loc_note: Optional[str] = None


@dataclass(slots=True)
class Event:
    """MapStory 的核心事件模型。"""

    id: Optional[int] = None
    time: TimeInfo = field(default_factory=TimeInfo)
    location: Location = field(default_factory=Location)
    persons: List[str] = field(default_factory=list)
    event: str = ""
    priority: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
