"""Excel 导入实现。"""

from typing import List

from ..models import Event
from .parsers import ImportParser


class ExcelParser(ImportParser):
    """Excel 文件导入实现占位。"""

    def parse(self, source) -> List[Event]:
        """解析 Excel 文件。"""
        raise NotImplementedError("Excel 导入尚未实现")
