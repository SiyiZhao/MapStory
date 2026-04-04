"""事件存储层。"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import List, Optional, Sequence

from .errors import NotFoundError
from .time_utils import parse_time_components, utc_now_iso
from .validators import (
    normalize_numeric_range,
    normalize_optional_text,
    normalize_persons,
    validate_coordinates,
    validate_event_text,
    validate_priority,
)

logger = logging.getLogger(__name__)


class EventStore:
    """封装事件表的 CRUD 与检索逻辑。"""

    def __init__(self, db_path: Path) -> None:
        """初始化数据库连接并确保表结构可用。"""
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """创建并迁移 events 表。"""
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_iso TEXT,
                time_year INTEGER,
                time_month INTEGER,
                time_day INTEGER,
                time_sort_bucket INTEGER NOT NULL DEFAULT 3,
                time_note TEXT,
                lat REAL,
                lon REAL,
                location_note TEXT,
                persons TEXT,
                event TEXT NOT NULL,
                priority TEXT,
                remark TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                deleted_at TEXT
            )
            """
        )
        existing_cols = {row[1] for row in cur.execute("PRAGMA table_info(events)").fetchall()}
        if "time_month" not in existing_cols:
            cur.execute("ALTER TABLE events ADD COLUMN time_month INTEGER")
        if "time_day" not in existing_cols:
            cur.execute("ALTER TABLE events ADD COLUMN time_day INTEGER")
        if "time_sort_bucket" not in existing_cols:
            cur.execute("ALTER TABLE events ADD COLUMN time_sort_bucket INTEGER NOT NULL DEFAULT 3")
        if "deleted_at" not in existing_cols:
            cur.execute("ALTER TABLE events ADD COLUMN deleted_at TEXT")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_time_year ON events(time_year)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_time_iso ON events(time_iso)")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_time_sort ON events(time_sort_bucket, time_year, time_month, time_day)"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_persons ON events(persons)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_location ON events(lat, lon)")

        rows = cur.execute("SELECT id, time_iso FROM events").fetchall()
        for row in rows:
            year, month, day, bucket = parse_time_components(row["time_iso"])
            cur.execute(
                """
                UPDATE events
                SET time_year = ?, time_month = ?, time_day = ?, time_sort_bucket = ?
                WHERE id = ?
                """,
                (year, month, day, bucket, row["id"]),
            )
        self.conn.commit()

    def create_event(
        self,
        *,
        time_iso: Optional[str],
        time_note: Optional[str],
        lat: Optional[float],
        lon: Optional[float],
        location_note: Optional[str],
        persons: Optional[str],
        event: str,
        priority: Optional[str],
        remark: Optional[str],
    ) -> int:
        """创建事件并返回新 ID。"""
        event_value = validate_event_text(event)
        validate_coordinates(lat, lon)

        now = utc_now_iso()
        time_iso_norm = normalize_optional_text(time_iso)
        year, month, day, bucket = parse_time_components(time_iso_norm)

        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO events (
                    time_iso, time_year, time_month, time_day, time_sort_bucket,
                    time_note, lat, lon, location_note, persons, event, priority, remark,
                    created_at, updated_at, deleted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    time_iso_norm,
                    year,
                    month,
                    day,
                    bucket,
                    normalize_optional_text(time_note),
                    lat,
                    lon,
                    normalize_optional_text(location_note),
                    normalize_persons(persons),
                    event_value,
                    validate_priority(priority),
                    normalize_optional_text(remark),
                    now,
                    now,
                ),
            )
        except sqlite3.Error as exc:
            logger.exception("Failed to create event")
            raise RuntimeError(f"数据库写入失败: {exc}") from exc
        self.conn.commit()
        return cur.lastrowid

    def add_event(
        self,
        *,
        time_iso: Optional[str],
        time_note: Optional[str],
        lat: Optional[float],
        lon: Optional[float],
        location_note: Optional[str],
        persons: Optional[str],
        event: str,
        priority: Optional[str],
        remark: Optional[str],
    ) -> int:
        """兼容旧接口，内部转调 create_event。"""
        return self.create_event(
            time_iso=time_iso,
            time_note=time_note,
            lat=lat,
            lon=lon,
            location_note=location_note,
            persons=persons,
            event=event,
            priority=priority,
            remark=remark,
        )

    def get_event(self, event_id: int) -> sqlite3.Row:
        """按 ID 获取单条事件。"""
        cur = self.conn.cursor()
        try:
            row = cur.execute(
                """
                SELECT id, time_iso, time_note, lat, lon, location_note, persons, event, priority, remark
                      , created_at, updated_at
                FROM events
                WHERE id = ? AND deleted_at IS NULL
                """,
                (event_id,),
            ).fetchone()
        except sqlite3.Error as exc:
            logger.exception("Failed to fetch event #%s", event_id)
            raise RuntimeError(f"数据库查询失败: {exc}") from exc
        if row is None:
            raise NotFoundError(f"事件不存在: {event_id}")
        return row

    def update_event(self, event_id: int, **fields: Optional[object]) -> int:
        """更新事件字段并返回影响行数。"""
        if not fields:
            return 0

        lat_value = fields.get("lat")
        lon_value = fields.get("lon")
        if lat_value is not None or lon_value is not None:
            validate_coordinates(
                float(lat_value) if lat_value is not None else None,
                float(lon_value) if lon_value is not None else None,
            )

        payload = {}
        for key, value in fields.items():
            if value is None:
                continue
            if key == "persons":
                payload[key] = normalize_persons(str(value))
            elif key == "time_iso":
                normalized = normalize_optional_text(str(value))
                year, month, day, bucket = parse_time_components(normalized)
                payload[key] = normalized
                payload["time_year"] = year
                payload["time_month"] = month
                payload["time_day"] = day
                payload["time_sort_bucket"] = bucket
            elif key == "priority":
                payload[key] = validate_priority(str(value))
            elif key == "event":
                payload[key] = validate_event_text(str(value))
            elif key in ("time_note", "location_note", "remark"):
                payload[key] = normalize_optional_text(str(value))
            else:
                payload[key] = value

        if not payload:
            return 0

        payload["updated_at"] = utc_now_iso()
        assignments = ", ".join(f"{k} = ?" for k in payload.keys())
        params = list(payload.values()) + [event_id]
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"UPDATE events SET {assignments} WHERE id = ? AND deleted_at IS NULL",
                params,
            )
        except sqlite3.Error as exc:
            logger.exception("Failed to update event #%s", event_id)
            raise RuntimeError(f"数据库更新失败: {exc}") from exc
        self.conn.commit()
        return cur.rowcount

    def delete_event(self, event_id: int, *, hard: bool = False) -> int:
        """删除事件，默认软删除。"""
        cur = self.conn.cursor()
        try:
            if hard:
                cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
            else:
                cur.execute(
                    "UPDATE events SET deleted_at = ?, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
                    (utc_now_iso(), utc_now_iso(), event_id),
                )
        except sqlite3.Error as exc:
            logger.exception("Failed to delete event #%s", event_id)
            raise RuntimeError(f"数据库删除失败: {exc}") from exc
        self.conn.commit()
        if cur.rowcount == 0:
            raise NotFoundError(f"事件不存在: {event_id}")
        return cur.rowcount

    def list_events(self, *, limit: int = 20, offset: int = 0, order: str = "time") -> List[sqlite3.Row]:
        """返回事件列表。"""
        if limit <= 0:
            raise ValueError("limit 必须为正整数")
        if offset < 0:
            raise ValueError("offset 不能为负数")
        if order not in {"time", "created"}:
            raise ValueError("order 仅支持 time 或 created")

        order_by = (
            "time_sort_bucket, time_year, COALESCE(time_month, 0), COALESCE(time_day, 0), id DESC"
            if order == "time"
            else "created_at DESC, id DESC"
        )
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"""
                SELECT id, time_iso, time_note, lat, lon, location_note, persons, event, priority, remark, created_at, updated_at
                FROM events
                WHERE deleted_at IS NULL
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        except sqlite3.Error as exc:
            logger.exception("Failed to list events")
            raise RuntimeError(f"数据库查询失败: {exc}") from exc
        return cur.fetchall()

    def create(self, *args, **kwargs):
        """设计文档中的 create 接口别名。"""
        return self.create_event(*args, **kwargs)

    def read(self, event_id: int):
        """设计文档中的 read 接口别名。"""
        return self.get_event(event_id)

    def update(self, event_id: int, event=None, **fields):
        """设计文档中的 update 接口别名。"""
        if event is not None:
            fields["event"] = event
        return self.update_event(event_id, **fields)

    def delete(self, event_id: int) -> int:
        """设计文档中的 delete 接口别名。"""
        return self.delete_event(event_id)

    def list_all(self, sort_by: str = "time", limit: int = None) -> List[sqlite3.Row]:
        """按设计文档返回事件列表。"""
        return self.list_events(limit=limit or 1000000, order="time" if sort_by == "time" else "created")

    def filter(self, filters: dict):
        """按复合条件过滤事件。"""
        return self.search_events(
            start_year=filters.get("start_year"),
            end_year=filters.get("end_year"),
            lat_range=filters.get("lat_range"),
            lon_range=filters.get("lon_range"),
            person_contains=filters.get("person_contains"),
            event_contains=filters.get("event_contains"),
            location_contains=filters.get("location_contains"),
            priority=filters.get("priority"),
            limit=filters.get("limit", 100),
            offset=filters.get("offset", 0),
            order=filters.get("order", "time"),
        )

    def query_by_time_range(self, start: str, end: str):
        """按时间范围查询。"""
        start_year = parse_time_components(start)[0]
        end_year = parse_time_components(end)[0]
        return self.search_events(start_year=start_year, end_year=end_year)

    def query_by_location_coords(self, lat: float, lon: float, radius_km: float):
        """按经纬度范围查询。"""
        lat_range = (lat - radius_km, lat + radius_km)
        lon_range = (lon - radius_km, lon + radius_km)
        return self.search_events(lat_range=lat_range, lon_range=lon_range)

    def query_by_location_name(self, region_name: str):
        """按地点名称查询。"""
        return self.search_events(location_contains=region_name)

    def query_by_persons(self, persons, match_all: bool = False):
        """按人物查询。"""
        if not persons:
            return []
        if isinstance(persons, str):
            return self.search_events(person_contains=persons)
        results = []
        for person in persons:
            rows = self.search_events(person_contains=person)
            if match_all:
                if not results:
                    results = rows
                else:
                    ids = {row["id"] for row in rows}
                    results = [row for row in results if row["id"] in ids]
            else:
                results.extend(rows)
        return results

    def query_by_priority(self, priority: str):
        """按优先级查询。"""
        return self.search_events(priority=priority)

    def search_events(
        self,
        *,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        lat_range: Optional[Sequence[float]] = None,
        lon_range: Optional[Sequence[float]] = None,
        person_contains: Optional[str] = None,
        event_contains: Optional[str] = None,
        location_contains: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order: str = "time",
    ) -> List[sqlite3.Row]:
        """按多条件检索事件。"""
        if limit <= 0:
            raise ValueError("limit 必须为正整数")
        if offset < 0:
            raise ValueError("offset 不能为负数")
        if order not in {"time", "created"}:
            raise ValueError("order 仅支持 time 或 created")

        conditions = ["deleted_at IS NULL"]
        params: List[object] = []

        if start_year is not None:
            conditions.append("time_year >= ?")
            params.append(start_year)
        if end_year is not None:
            conditions.append("time_year <= ?")
            params.append(end_year)

        lat_norm = normalize_numeric_range(lat_range, label="lat_range", min_value=-90, max_value=90)
        if lat_norm:
            conditions.append("lat BETWEEN ? AND ?")
            params.extend(lat_norm)

        lon_norm = normalize_numeric_range(lon_range, label="lon_range", min_value=-180, max_value=180)
        if lon_norm:
            conditions.append("lon BETWEEN ? AND ?")
            params.extend(lon_norm)

        if person_contains:
            conditions.append("persons LIKE ?")
            params.append(f"%{person_contains}%")
        if event_contains:
            conditions.append("event LIKE ?")
            params.append(f"%{event_contains}%")
        if location_contains:
            conditions.append("location_note LIKE ?")
            params.append(f"%{location_contains}%")
        if priority:
            conditions.append("priority = ?")
            params.append(validate_priority(priority))

        order_by = (
            "time_sort_bucket, time_year, COALESCE(time_month, 0), COALESCE(time_day, 0), id DESC"
            if order == "time"
            else "created_at DESC, id DESC"
        )
        where_clause = " AND ".join(conditions)

        cur = self.conn.cursor()
        try:
            cur.execute(
                f"""
                SELECT id, time_iso, time_note, lat, lon, location_note, persons, event, priority, remark, created_at, updated_at
                FROM events
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            )
        except sqlite3.Error as exc:
            logger.exception("Failed to search events")
            raise RuntimeError(f"数据库检索失败: {exc}") from exc
        return cur.fetchall()
