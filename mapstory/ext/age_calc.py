"""人物年龄计算。"""

from typing import Optional


def calculate_age(birth_year: Optional[int], event_year: Optional[int]) -> Optional[int]:
    """根据生年和事件年计算年龄。"""
    if birth_year is None or event_year is None:
        return None
    return event_year - birth_year
