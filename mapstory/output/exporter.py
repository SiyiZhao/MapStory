"""导出功能。"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .formatters import to_csv, to_json


class Exporter:
    """统一导出管理器。"""

    def export(self, rows: Iterable, format: str, output_path: str) -> None:
        """将事件导出到指定文件。"""
        path = Path(output_path)
        if format == "json":
            path.write_text(to_json(rows), encoding="utf-8")
            return
        if format == "csv":
            path.write_text(to_csv(rows), encoding="utf-8")
            return
        raise NotImplementedError(f"暂不支持导出格式: {format}")
