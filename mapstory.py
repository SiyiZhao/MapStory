#!/usr/bin/env python3
"""
MapStory core functionality: CLI for storing, updating, and querying events.
"""
import argparse
import datetime as _dt
import logging
import numbers
import re
import sqlite3
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


DEFAULT_DB = "mapstory.db"


PRIORITY_CHOICES = {
    "fact": "史实",
    "doubt": "史实（存疑）",
    "fanon": "自设",
    "abridged_fact": "史实（删减）",
}

PRIORITY_LABELS = set(PRIORITY_CHOICES.values())


logger = logging.getLogger(__name__)


class InputValidationError(ValueError):
    """Raised when user input fails data model validation."""


def _utc_now_iso() -> str:
    return _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _parse_year(value: Optional[str]) -> Optional[int]:
    """Extract a leading signed year if present; otherwise return None."""
    if not value:
        return None


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _parse_time_components(value: Optional[str]) -> Tuple[Optional[int], Optional[int], Optional[int], int]:
    """
    Parse supported time formats and return (year, month, day, sort_bucket).
    sort_bucket: 0=precise(day), 1=fuzzy(year/month or year), 2=conflict(unparseable), 3=empty
    """
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None, None, None, 3

    match = re.fullmatch(r"([+-]?\d{1,6})(?:-(\d{1,2})(?:-(\d{1,2}))?)?", normalized)
    if not match:
        return _parse_year(normalized), None, None, 2

    year = int(match.group(1))
    month_raw = match.group(2)
    day_raw = match.group(3)

    if month_raw is None:
        return year, None, None, 1

    month = int(month_raw)
    if month < 1 or month > 12:
        return year, None, None, 2

    if day_raw is None:
        return year, month, None, 1

    day = int(day_raw)
    if day < 1 or day > 31:
        return year, month, None, 2
    return year, month, day, 0


def _validate_priority(priority: Optional[str]) -> Optional[str]:
    if priority is None:
        return None
    raw = _normalize_optional_text(priority)
    if raw is None:
        return None
    if raw in PRIORITY_CHOICES:
        return PRIORITY_CHOICES[raw]
    if raw in PRIORITY_LABELS:
        return raw
    raise InputValidationError(
        "priority 必须为 fact/doubt/fanon/abridged_fact 或对应中文标签"
    )


def _validate_event_text(event: Optional[str]) -> str:
    value = _normalize_optional_text(event)
    if value is None:
        raise InputValidationError("event 不能为空")
    return value


def _validate_coordinates(lat: Optional[float], lon: Optional[float]) -> None:
    if lat is not None and (lat < -90 or lat > 90):
        raise InputValidationError("lat 超出范围，必须在 -90 到 90 之间")
    if lon is not None and (lon < -180 or lon > 180):
        raise InputValidationError("lon 超出范围，必须在 -180 到 180 之间")


def _normalize_numeric_range(
    values: Optional[Sequence[float]],
    *,
    label: str,
    min_value: float,
    max_value: float,
) -> Optional[Tuple[float, float]]:
    if not values:
        return None
    if len(values) != 2:
        raise InputValidationError(f"{label} 需要两个值")
    start = float(values[0])
    end = float(values[1])
    if start > end:
        start, end = end, start
    if start < min_value or end > max_value:
        raise InputValidationError(f"{label} 超出范围，允许区间为 {min_value} 到 {max_value}")
    return (start, end)
    match = re.match(r"^\s*([+-]?\d{1,6})", value)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _normalize_persons(raw: Optional[str]) -> str:
    if not raw:
        return ""
    parts = [p.strip() for p in re.split(r"[;,]", raw) if p.strip()]
    return ", ".join(parts)


def _print_rows(rows: Sequence[sqlite3.Row]) -> None:
    if not rows:
        print("(no results)")
        return
    # Keys must match SQL select column names.
    keys = ["id", "time_iso", "time_note", "lat", "lon", "location_note", "persons", "event", "priority", "remark"]
    headers = {"time_iso": "time", "time_note": "time_note", "location_note": "location", "persons": "persons", "event": "event", "priority": "priority", "remark": "remark", "lat": "lat", "lon": "lon", "id": "id"}
    col_widths = {k: max(len(headers[k]), *(len(str(row[k])) if row[k] is not None else 0 for row in rows)) for k in keys}
    print(" | ".join(headers[k].ljust(col_widths[k]) for k in keys))
    print("-+-".join("-" * col_widths[k] for k in keys))
    for row in rows:
        print(" | ".join(str(row[k]).ljust(col_widths[k]) if row[k] is not None else "".ljust(col_widths[k]) for k in keys))


class EventStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
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
                updated_at TEXT NOT NULL
            )
            """
        )
        existing_cols = {
            row[1] for row in cur.execute("PRAGMA table_info(events)").fetchall()
        }
        if "time_month" not in existing_cols:
            cur.execute("ALTER TABLE events ADD COLUMN time_month INTEGER")
        if "time_day" not in existing_cols:
            cur.execute("ALTER TABLE events ADD COLUMN time_day INTEGER")
        if "time_sort_bucket" not in existing_cols:
            cur.execute("ALTER TABLE events ADD COLUMN time_sort_bucket INTEGER NOT NULL DEFAULT 3")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_time_year ON events(time_year)")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_time_sort ON events(time_sort_bucket, time_year, time_month, time_day)"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_persons ON events(persons)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_location ON events(lat, lon)")
        # Backfill derived time-ordering fields for existing rows.
        rows = cur.execute("SELECT id, time_iso FROM events").fetchall()
        for row in rows:
            time_year, time_month, time_day, time_sort_bucket = _parse_time_components(row["time_iso"])
            cur.execute(
                """
                UPDATE events
                SET time_year = ?, time_month = ?, time_day = ?, time_sort_bucket = ?
                WHERE id = ?
                """,
                (time_year, time_month, time_day, time_sort_bucket, row["id"]),
            )
        self.conn.commit()

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
        event_value = _validate_event_text(event)
        _validate_coordinates(lat, lon)

        now = _utc_now_iso()
        time_iso_norm = _normalize_optional_text(time_iso)
        time_year, time_month, time_day, time_sort_bucket = _parse_time_components(time_iso_norm)
        persons_norm = _normalize_persons(persons)
        priority_value = _validate_priority(priority)
        time_note_norm = _normalize_optional_text(time_note)
        location_note_norm = _normalize_optional_text(location_note)
        remark_norm = _normalize_optional_text(remark)
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO events (time_iso, time_year, time_month, time_day, time_sort_bucket, time_note, lat, lon, location_note, persons, event, priority, remark, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time_iso_norm,
                    time_year,
                    time_month,
                    time_day,
                    time_sort_bucket,
                    time_note_norm,
                    lat,
                    lon,
                    location_note_norm,
                    persons_norm,
                    event_value,
                    priority_value,
                    remark_norm,
                    now,
                    now,
                ),
            )
        except sqlite3.Error as exc:
            logger.exception("Failed to insert event")
            raise RuntimeError(f"数据库写入失败: {exc}") from exc
        self.conn.commit()
        return cur.lastrowid

    def update_event(self, event_id: int, **fields: Optional[object]) -> int:
        if not fields:
            return 0
        payload = {}
        lat_value = fields.get("lat")
        lon_value = fields.get("lon")
        if lat_value is not None or lon_value is not None:
            _validate_coordinates(
                float(lat_value) if isinstance(lat_value, numbers.Real) else None,
                float(lon_value) if isinstance(lon_value, numbers.Real) else None,
            )

        for key, value in fields.items():
            if value is None:
                continue
            if key == "persons":
                payload[key] = _normalize_persons(value)  # type: ignore[assignment]
            elif key == "time_iso":
                normalized = _normalize_optional_text(str(value))
                time_year, time_month, time_day, time_sort_bucket = _parse_time_components(normalized)
                payload[key] = normalized
                payload["time_year"] = time_year
                payload["time_month"] = time_month
                payload["time_day"] = time_day
                payload["time_sort_bucket"] = time_sort_bucket
            elif key == "priority":
                payload[key] = _validate_priority(str(value))
            elif key == "event":
                payload[key] = _validate_event_text(str(value))
            elif key in ("time_note", "location_note", "remark"):
                payload[key] = _normalize_optional_text(str(value))
            else:
                payload[key] = value
        if not payload:
            return 0
        payload["updated_at"] = _utc_now_iso()
        assignments = ", ".join(f"{k} = ?" for k in payload.keys())
        params = list(payload.values()) + [event_id]
        cur = self.conn.cursor()
        try:
            cur.execute(f"UPDATE events SET {assignments} WHERE id = ?", params)
        except sqlite3.Error as exc:
            logger.exception("Failed to update event #%s", event_id)
            raise RuntimeError(f"数据库更新失败: {exc}") from exc
        self.conn.commit()
        return cur.rowcount

    def list_events(self, limit: int = 20) -> List[sqlite3.Row]:
        if limit <= 0:
            raise InputValidationError("limit 必须为正整数")
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, time_iso, time_note, lat, lon, location_note, persons, event, priority, remark
                FROM events
                ORDER BY time_sort_bucket, time_year, COALESCE(time_month, 0), COALESCE(time_day, 0), id DESC
                LIMIT ?
                """,
                (limit,),
            )
        except sqlite3.Error as exc:
            logger.exception("Failed to list events")
            raise RuntimeError(f"数据库查询失败: {exc}") from exc
        return cur.fetchall()

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
    ) -> List[sqlite3.Row]:
        conditions: List[str] = []
        params: List[object] = []
        if start_year is not None:
            conditions.append("time_year >= ?")
            params.append(start_year)
        if end_year is not None:
            conditions.append("time_year <= ?")
            params.append(end_year)
        lat_range_norm = _normalize_numeric_range(lat_range, label="lat_range", min_value=-90, max_value=90)
        if lat_range_norm:
            conditions.append("lat BETWEEN ? AND ?")
            params.extend(lat_range_norm)
        lon_range_norm = _normalize_numeric_range(lon_range, label="lon_range", min_value=-180, max_value=180)
        if lon_range_norm:
            conditions.append("lon BETWEEN ? AND ?")
            params.extend(lon_range_norm)
        if person_contains:
            conditions.append("persons LIKE ?")
            params.append(f"%{person_contains}%")
        if event_contains:
            conditions.append("event LIKE ?")
            params.append(f"%{event_contains}%")
        if location_contains:
            conditions.append("location_note LIKE ?")
            params.append(f"%{location_contains}%")
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"""
                SELECT id, time_iso, time_note, lat, lon, location_note, persons, event, priority, remark
                FROM events
                {where_clause}
                ORDER BY time_sort_bucket, time_year, COALESCE(time_month, 0), COALESCE(time_day, 0), id DESC
                """,
                params,
            )
        except sqlite3.Error as exc:
            logger.exception("Failed to search events")
            raise RuntimeError(f"数据库检索失败: {exc}") from exc
        return cur.fetchall()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MapStory core functions")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to SQLite database file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_p = subparsers.add_parser("add", help="Add a new event")
    add_p.add_argument("--event", required=True, help="Event description")
    add_p.add_argument("--time", dest="time_iso", help="ISO-like time string (e.g., 1949-10-01)")
    add_p.add_argument("--time-note", help="Historical calendar note")
    add_p.add_argument("--lat", type=float, help="Latitude")
    add_p.add_argument("--lon", type=float, help="Longitude")
    add_p.add_argument("--location-note", help="Place name or admin division")
    add_p.add_argument("--persons", help="Comma- or semicolon-separated people")
    add_p.add_argument(
        "--priority",
        choices=list(PRIORITY_CHOICES.keys()),
        help="Priority: fact, doubt, fanon, abridged_fact",
    )
    add_p.add_argument("--remark", help="Source or extra note")

    upd_p = subparsers.add_parser("update", help="Update an existing event")
    upd_p.add_argument("id", type=int, help="Event ID")
    upd_p.add_argument("--event", help="Event description")
    upd_p.add_argument("--time", dest="time_iso", help="ISO-like time string")
    upd_p.add_argument("--time-note", help="Historical calendar note")
    upd_p.add_argument("--lat", type=float, help="Latitude")
    upd_p.add_argument("--lon", type=float, help="Longitude")
    upd_p.add_argument("--location-note", help="Place name or admin division")
    upd_p.add_argument("--persons", help="Comma- or semicolon-separated people")
    upd_p.add_argument(
        "--priority",
        choices=list(PRIORITY_CHOICES.keys()),
        help="Priority: fact, doubt, fanon, abridged_fact",
    )
    upd_p.add_argument("--remark", help="Source or extra note")

    list_p = subparsers.add_parser("list", help="List recent events")
    list_p.add_argument("--limit", type=int, default=20, help="Number of rows")

    search_p = subparsers.add_parser("search", help="Search by filters")
    search_p.add_argument("--start-year", type=int, help="Start year (inclusive)")
    search_p.add_argument("--end-year", type=int, help="End year (inclusive)")
    search_p.add_argument("--lat-range", nargs=2, type=float, metavar=("MIN", "MAX"), help="Latitude range")
    search_p.add_argument("--lon-range", nargs=2, type=float, metavar=("MIN", "MAX"), help="Longitude range")
    search_p.add_argument("--person", help="Person substring")
    search_p.add_argument("--event", dest="event_contains", help="Event substring")
    search_p.add_argument("--location", dest="location_contains", help="Location substring")

    return parser


def handle_add(store: EventStore, args: argparse.Namespace) -> None:
    event_id = store.add_event(
        time_iso=args.time_iso,
        time_note=args.time_note,
        lat=args.lat,
        lon=args.lon,
        location_note=args.location_note,
        persons=args.persons,
        event=args.event,
        priority=args.priority,
        remark=args.remark,
    )
    print(f"created event #{event_id}")


def handle_update(store: EventStore, args: argparse.Namespace) -> None:
    updated = store.update_event(
        args.id,
        event=args.event,
        time_iso=args.time_iso,
        time_note=args.time_note,
        lat=args.lat,
        lon=args.lon,
        location_note=args.location_note,
        persons=args.persons,
        priority=args.priority,
        remark=args.remark,
    )
    if updated:
        print(f"updated event #{args.id}")
    else:
        print(f"no changes applied to #{args.id}")


def handle_list(store: EventStore, args: argparse.Namespace) -> None:
    rows = store.list_events(limit=args.limit)
    _print_rows(rows)


def handle_search(store: EventStore, args: argparse.Namespace) -> None:
    rows = store.search_events(
        start_year=args.start_year,
        end_year=args.end_year,
        lat_range=args.lat_range,
        lon_range=args.lon_range,
        person_contains=args.person,
        event_contains=args.event_contains,
        location_contains=args.location_contains,
    )
    _print_rows(rows)


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = EventStore(Path(args.db))
    try:
        if args.command == "add":
            handle_add(store, args)
        elif args.command == "update":
            handle_update(store, args)
        elif args.command == "list":
            handle_list(store, args)
        elif args.command == "search":
            handle_search(store, args)
        else:
            parser.error("Unknown command")
    except InputValidationError as exc:
        parser.error(f"输入错误: {exc}")
    except RuntimeError as exc:
        parser.error(str(exc))


def interactive():
    print("=== MapStory 交互模式 ===")
    db = input(f"数据库文件名（默认: {DEFAULT_DB}）：").strip() or DEFAULT_DB
    store = EventStore(Path(db))
    while True:
        print("\n请选择操作: [add] 新增 | [list] 查看 | [update] 更新 | [search] 检索 | [exit] 退出")
        cmd = input("操作: ").strip().lower()
        if cmd in ("exit", "quit", "q"):
            print("再见！")
            break
        elif cmd == "add":
            print("请输入各字段（可回车跳过可选项）:")
            event = input("事件描述（必填）: ").strip()
            if not event:
                print("事件描述不能为空！")
                continue
            time_iso = input("时间（如-221或-221-06-01，可空）: ").strip() or None
            time_note = input("时间备注（如秦王政二十六年，可空）: ").strip() or None
            lat = input("纬度lat（可空）: ").strip()
            lat = float(lat) if lat else None
            lon = input("经度lon（可空）: ").strip()
            lon = float(lon) if lon else None
            location_note = input("地点备注（可空）: ").strip() or None
            persons = input("人物（逗号/分号分隔，可空）: ").strip() or None
            priority = input("优先级 [fact/doubt/fanon/abridged_fact]（可空）: ").strip() or None
            remark = input("备注（可空）: ").strip() or None
            try:
                eid = store.add_event(
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
                print(f"已添加事件 #{eid}")
            except (InputValidationError, RuntimeError) as exc:
                print(f"输入/存储失败：{exc}")
        elif cmd == "list":
            limit = input("显示多少条（默认20）: ").strip()
            limit = int(limit) if limit else 20
            try:
                rows = store.list_events(limit=limit)
                _print_rows(rows)
            except (InputValidationError, RuntimeError) as exc:
                print(f"查询失败：{exc}")
        elif cmd == "update":
            try:
                eid = int(input("要更新的事件ID: ").strip())
            except Exception:
                print("ID 必须为数字！")
                continue
            # 显示现有条目
            row = None
            try:
                row = store.conn.execute(
                    "SELECT id, time_iso, time_note, lat, lon, location_note, persons, event, priority, remark FROM events WHERE id = ?",
                    (eid,)
                ).fetchone()
            except Exception:
                pass
            if not row:
                print(f"未找到ID为 {eid} 的事件。")
                continue
            print("现有条目：")
            for k in ["id", "time_iso", "time_note", "lat", "lon", "location_note", "persons", "event", "priority", "remark"]:
                print(f"  {k}: {row[k]}")
            print("留空则不修改该字段。")
            fields = {}
            for k, prompt in [
                ("event", "新事件描述"),
                ("time_iso", "新时间"),
                ("time_note", "新时间备注"),
                ("lat", "新纬度lat"),
                ("lon", "新经度lon"),
                ("location_note", "新地点备注"),
                ("persons", "新人物"),
                ("priority", "新优先级"),
                ("remark", "新备注")]:
                v = input(f"{prompt}: ").strip()
                if v:
                    if k in ("lat", "lon"):
                        try:
                            v = float(v)
                        except Exception:
                            print(f"{prompt} 需为数字，已跳过")
                            continue
                    fields[k] = v
            try:
                n = store.update_event(eid, **fields)
                print(f"已更新 {n} 条记录")
            except (InputValidationError, RuntimeError) as exc:
                print(f"更新失败：{exc}")
        elif cmd == "search":
            print("可输入过滤条件，留空则忽略。")
            start_year = input("起始年份: ").strip()
            end_year = input("结束年份: ").strip()
            lat_range = input("纬度范围（如30,40）: ").strip()
            lon_range = input("经度范围（如100,120）: ").strip()
            person = input("人物包含: ").strip() or None
            event_contains = input("事件包含: ").strip() or None
            location_contains = input("地点包含: ").strip() or None
            kwargs = {}
            if start_year: kwargs["start_year"] = int(start_year)
            if end_year: kwargs["end_year"] = int(end_year)
            if lat_range:
                try:
                    lat1, lat2 = map(float, lat_range.split(","))
                    kwargs["lat_range"] = (lat1, lat2)
                except Exception:
                    print("纬度范围格式错误，已忽略")
            if lon_range:
                try:
                    lon1, lon2 = map(float, lon_range.split(","))
                    kwargs["lon_range"] = (lon1, lon2)
                except Exception:
                    print("经度范围格式错误，已忽略")
            if person: kwargs["person_contains"] = person
            if event_contains: kwargs["event_contains"] = event_contains
            if location_contains: kwargs["location_contains"] = location_contains
            try:
                rows = store.search_events(**kwargs)
                _print_rows(rows)
            except (InputValidationError, RuntimeError) as exc:
                print(f"检索失败：{exc}")
        else:
            print("未知操作，请重试。")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        interactive()
    else:
        main()
