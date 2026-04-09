"""终端输出格式化函数。"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from typing import Iterable, Sequence

from ..constants import EVENT_COLUMNS
from ..time import format_structured_time, structured_time_from_parts


def row_to_dict(row: sqlite3.Row) -> dict:
    """将 sqlite 行转换为普通字典。"""
    data = {}
    if "id" in row.keys():
        data["id"] = row["id"]
    data["time"] = _row_time_text(row)
    for key in EVENT_COLUMNS:
        if key in {"id", "time"}:
            continue
        if key in row.keys():
            data[key] = row[key]
    return data


def format_event_table(rows: Sequence[sqlite3.Row]) -> str:
    """将事件列表格式化为表格字符串。"""
    if not rows:
        return "(no results)"
    headers = {
        "id": "id",
        "time": "time",
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
        key: max(len(headers[key]), *(len(_table_value(row, key)) for row in rows))
        for key in EVENT_COLUMNS
    }
    lines = [
        " | ".join(headers[k].ljust(widths[k]) for k in EVENT_COLUMNS),
        "-+-".join("-" * widths[k] for k in EVENT_COLUMNS),
    ]
    for row in rows:
        lines.append(" | ".join(_table_value(row, k).ljust(widths[k]) for k in EVENT_COLUMNS))
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


def _row_time_text(row: sqlite3.Row) -> str:
    """从数据库行生成展示时间。"""
    if "time" in row.keys():
        return row["time"] or ""
    value = structured_time_from_parts(
        year=row["time_year"] if "time_year" in row.keys() else None,
        month=row["time_month"] if "time_month" in row.keys() else None,
        day=row["time_day"] if "time_day" in row.keys() else None,
        hour=row["time_hour"] if "time_hour" in row.keys() else None,
        minute=row["time_minute"] if "time_minute" in row.keys() else None,
    )
    return format_structured_time(value)


def _table_value(row: sqlite3.Row, key: str) -> str:
    """生成表格单元格文本。"""
    if key == "time":
        return _row_time_text(row)
    value = row[key] if key in row.keys() else None
    return "" if value is None else str(value)
