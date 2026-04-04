"""交互模式入口。"""

from __future__ import annotations

from pathlib import Path

from ..constants import DEFAULT_DB
from ..errors import InputValidationError, NotFoundError
from ..output import print_rows_table
from ..store import EventStore


def interactive() -> None:
    """提供简化的文本交互界面。"""
    print("=== MapStory 交互模式 ===")
    db = input(f"数据库文件名（默认: {DEFAULT_DB}）：").strip() or DEFAULT_DB
    store = EventStore(Path(db))

    while True:
        print("\n请选择操作: [create] [list] [get] [update] [delete] [search] [exit]")
        cmd = input("操作: ").strip().lower()

        if cmd in {"exit", "quit", "q"}:
            print("再见！")
            return

        try:
            if cmd == "create":
                _do_create(store)
            elif cmd == "list":
                _do_list(store)
            elif cmd == "get":
                _do_get(store)
            elif cmd == "update":
                _do_update(store)
            elif cmd == "delete":
                _do_delete(store)
            elif cmd == "search":
                _do_search(store)
            else:
                print("未知操作，请重试。")
        except (InputValidationError, NotFoundError, RuntimeError, ValueError) as exc:
            print(f"操作失败：{exc}")


def _do_create(store: EventStore) -> None:
    """读取输入并创建事件。"""
    event = input("事件描述（必填）: ").strip()
    event_id = store.create_event(
        time_iso=input("时间（如-221或1949-10-01，可空）: ").strip() or None,
        time_note=input("时间备注（可空）: ").strip() or None,
        lat=_to_float(input("纬度lat（可空）: ").strip()),
        lon=_to_float(input("经度lon（可空）: ").strip()),
        location_note=input("地点备注（可空）: ").strip() or None,
        persons=input("人物（逗号/分号分隔，可空）: ").strip() or None,
        event=event,
        priority=input("优先级 [fact/doubt/fanon/abridged_fact]（可空）: ").strip() or None,
        remark=input("备注（可空）: ").strip() or None,
    )
    print_rows_table([store.get_event(event_id)])


def _do_list(store: EventStore) -> None:
    """列出最近事件。"""
    limit_raw = input("显示多少条（默认20）: ").strip()
    limit = int(limit_raw) if limit_raw else 20
    print_rows_table(store.list_events(limit=limit))


def _do_get(store: EventStore) -> None:
    """查看单条事件。"""
    event_id = int(input("事件ID: ").strip())
    print_rows_table([store.get_event(event_id)])


def _do_update(store: EventStore) -> None:
    """更新指定事件。"""
    event_id = int(input("要更新的事件ID: ").strip())
    fields = {
        "event": input("新事件描述（留空不改）: ").strip() or None,
        "time_iso": input("新时间（留空不改）: ").strip() or None,
        "time_note": input("新时间备注（留空不改）: ").strip() or None,
        "lat": _to_float(input("新纬度lat（留空不改）: ").strip(), allow_none=True),
        "lon": _to_float(input("新经度lon（留空不改）: ").strip(), allow_none=True),
        "location_note": input("新地点备注（留空不改）: ").strip() or None,
        "persons": input("新人物（留空不改）: ").strip() or None,
        "priority": input("新优先级（留空不改）: ").strip() or None,
        "remark": input("新备注（留空不改）: ").strip() or None,
    }
    store.update_event(event_id, **fields)
    print_rows_table([store.get_event(event_id)])


def _do_delete(store: EventStore) -> None:
    """删除指定事件。"""
    event_id = int(input("要删除的事件ID: ").strip())
    hard = input("是否硬删除？[y/N]: ").strip().lower() == "y"
    store.delete_event(event_id, hard=hard)
    print(f"已删除事件 #{event_id}")


def _do_search(store: EventStore) -> None:
    """按条件检索事件。"""
    start_year = input("起始年份（可空）: ").strip()
    end_year = input("结束年份（可空）: ").strip()
    person = input("人物包含（可空）: ").strip() or None
    event_contains = input("事件包含（可空）: ").strip() or None
    location = input("地点包含（可空）: ").strip() or None
    rows = store.search_events(
        start_year=int(start_year) if start_year else None,
        end_year=int(end_year) if end_year else None,
        person_contains=person,
        event_contains=event_contains,
        location_contains=location,
    )
    print_rows_table(rows)


def _to_float(raw: str, *, allow_none: bool = True):
    """将字符串转换为浮点数。"""
    if not raw and allow_none:
        return None
    return float(raw)
