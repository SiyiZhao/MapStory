"""维基百科导入实现。"""

from typing import List

from ..models import Event
from .parsers import ImportParser


class WikipediaParser(ImportParser):
    """维基百科导入占位实现。"""

    def parse(self, source) -> List[Event]:
        """解析维基百科来源。"""
        raise NotImplementedError("维基百科导入尚未实现")
