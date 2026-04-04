"""CLI 命令入口与处理逻辑。"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from ..constants import DEFAULT_DB, PRIORITY_CHOICES
from ..errors import InputValidationError, NotFoundError
from ..output import print_row_json, print_rows_json, print_rows_table
from ..store import EventStore
from . import commands


def build_parser() -> argparse.ArgumentParser:
    """构建 CLI 参数解析器。"""
    parser = argparse.ArgumentParser(description="MapStory CLI")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite database path")

    root = parser.add_subparsers(dest="resource", required=True)
    event = root.add_parser("event", help="Event resource commands")
    event_sub = event.add_subparsers(dest="action", required=True)

    create = event_sub.add_parser("create", help="Create event")
    _add_event_fields(create, required_event=True)

    update = event_sub.add_parser("update", help="Update event")
    update.add_argument("id", type=int, help="Event ID")
    _add_event_fields(update, required_event=False)

    get_cmd = event_sub.add_parser("get", help="Get one event")
    get_cmd.add_argument("id", type=int, help="Event ID")
    get_cmd.add_argument("--format", choices=["table", "json"], default="table")

    delete = event_sub.add_parser("delete", help="Delete one event")
    delete.add_argument("id", type=int, help="Event ID")
    delete.add_argument("--hard", action="store_true", help="Hard delete")

    list_cmd = event_sub.add_parser("list", help="List events")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)
    list_cmd.add_argument("--order", choices=["time", "created"], default="time")
    list_cmd.add_argument("--format", choices=["table", "json"], default="table")

    search = event_sub.add_parser("search", help="Search events")
    search.add_argument("--start-year", type=int)
    search.add_argument("--end-year", type=int)
    search.add_argument("--lat-range", nargs=2, type=float, metavar=("MIN", "MAX"))
    search.add_argument("--lon-range", nargs=2, type=float, metavar=("MIN", "MAX"))
    search.add_argument("--person")
    search.add_argument("--event", dest="event_contains")
    search.add_argument("--location", dest="location_contains")
    search.add_argument("--priority", choices=list(PRIORITY_CHOICES.keys()))
    search.add_argument("--limit", type=int, default=100)
    search.add_argument("--offset", type=int, default=0)
    search.add_argument("--order", choices=["time", "created"], default="time")
    search.add_argument("--format", choices=["table", "json"], default="table")

    return parser


def _add_event_fields(parser: argparse.ArgumentParser, *, required_event: bool) -> None:
    """为 create/update 命令注入事件字段参数。"""
    parser.add_argument("--event", required=required_event, help="Event description")
    parser.add_argument("--time", dest="time_iso")
    parser.add_argument("--time-note")
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lon", type=float)
    parser.add_argument("--location-note")
    parser.add_argument("--persons")
    parser.add_argument("--priority", choices=list(PRIORITY_CHOICES.keys()))
    parser.add_argument("--remark")
    parser.add_argument("--format", choices=["table", "json"], default="table")


def dispatch(args: argparse.Namespace) -> None:
    """按命令分派到事件处理器。"""
    store = EventStore(Path(args.db))
    if args.resource != "event":
        raise InputValidationError("仅支持 event 资源")

    if args.action == "create":
        rows = commands.create_event(store, args)
        _print_result(rows, args.format)
        return

    if args.action == "update":
        rows = commands.update_event(store, args)
        if not rows:
            raise NotFoundError(f"事件不存在或无变化: {args.id}")
        _print_result(rows, args.format)
        return

    if args.action == "get":
        rows = commands.get_event(store, args)
        _print_result(rows, args.format)
        return

    if args.action == "delete":
        commands.delete_event(store, args)
        print(f"deleted event #{args.id}")
        return

    if args.action == "list":
        rows = commands.list_events(store, args)
        _print_result(rows, args.format)
        return

    if args.action == "search":
        rows = commands.search_events(store, args)
        _print_result(rows, args.format)
        return

    raise InputValidationError(f"未知命令: {args.action}")


def _print_result(rows, output_format: str) -> None:
    """根据格式输出结果。"""
    if output_format == "json":
        print_rows_json(rows)
    else:
        print_rows_table(rows)


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI 主入口。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        dispatch(args)
    except (InputValidationError, ValueError) as exc:
        parser.error(f"输入错误: {exc}")
    except NotFoundError as exc:
        parser.error(str(exc))
    except RuntimeError as exc:
        parser.error(str(exc))
