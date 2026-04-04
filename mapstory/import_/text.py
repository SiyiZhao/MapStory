"""纯文本导入实现。"""

from typing import List

from ..models import Event
from .parsers import ImportParser


class TextParser(ImportParser):
    """纯文本导入占位实现。"""

    def parse(self, source) -> List[Event]:
        """解析纯文本源。"""
        raise NotImplementedError("纯文本导入尚未实现")
