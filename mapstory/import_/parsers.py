"""导入解析器基类。"""

from abc import ABC, abstractmethod
from typing import List

from ..models import Event


class ImportParser(ABC):
    """导入解析器基类。"""

    @abstractmethod
    def parse(self, source) -> List[Event]:
        """将输入源解析为事件列表。"""
        raise NotImplementedError
