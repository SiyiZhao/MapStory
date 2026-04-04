"""年号数据库占位实现。"""

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class EraRecord:
    """年号记录。"""

    name: str
    start_iso: str
    end_iso: Optional[str] = None


class EraDatabase:
    """年号查询占位实现。"""

    def find_by_name(self, name: str) -> Optional[EraRecord]:
        """按年号名查询。"""
        return None
