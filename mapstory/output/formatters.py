"""终端输出格式化函数。"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from typing import Iterable, Sequence

from ..constants import EVENT_COLUMNS


def row_to_dict(row: sqlite3.Row) -> dict:
    """将 sqlite 行转换为普通字典。"""
    return {key: row[key] for key in EVENT_COLUMNS if key in row.keys()}


def format_event_table(rows: Sequence[sqlite3.Row]) -> str:
    """将事件列表格式化为表格字符串。"""
    if not rows:
        return "(no results)"
    headers = {
        "id": "id",
        "time_iso": "time",
        "time_note": "time_note",
        "lat": "lat",
        "lon": "lon",
        "location_note": "location",
        "persons": "persons",
        "event": "event",
        "priority": "priority",
        "remark": "remark",
    }
    widths = {
        key: max(len(headers[key]), *(len(str(row[key])) if row[key] is not None else 0 for row in rows))
        for key in EVENT_COLUMNS
    }
    lines = [
        " | ".join(headers[k].ljust(widths[k]) for k in EVENT_COLUMNS),
        "-+-".join("-" * widths[k] for k in EVENT_COLUMNS),
    ]
    for row in rows:
        lines.append(" | ".join((str(row[k]) if row[k] is not None else "").ljust(widths[k]) for k in EVENT_COLUMNS))
    return "\n".join(lines)


def format_event_detail(row: sqlite3.Row) -> str:
    """将单条事件格式化为详情字符串。"""
    return json.dumps(row_to_dict(row), ensure_ascii=False, indent=2)


def to_json(rows: Iterable[sqlite3.Row]) -> str:
    """按 JSON 格式序列化事件列表。"""
    return json.dumps([row_to_dict(row) for row in rows], ensure_ascii=False, indent=2)


def to_csv(rows: Iterable[sqlite3.Row], tz: str = "Asia/Shanghai") -> str:
    """导出为 CSV 文本。"""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EVENT_COLUMNS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row_to_dict(row))
    return buffer.getvalue()


def print_rows_table(rows: Sequence[sqlite3.Row]) -> None:
    """按表格格式打印事件列表。"""
    print(format_event_table(rows))


def print_rows_json(rows: Iterable[sqlite3.Row]) -> None:
    """按 JSON 格式打印事件列表。"""
    print(to_json(rows))


def print_row_json(row: sqlite3.Row) -> None:
    """按 JSON 格式打印单条事件。"""
    print(format_event_detail(row))
