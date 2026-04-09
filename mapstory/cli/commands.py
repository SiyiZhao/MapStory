"""CLI 命令实现。"""

from argparse import Namespace

from ..store import EventStore


def create_event(store: EventStore, args: Namespace):
    """创建事件并返回创建后的记录。"""
    event_id = store.create_event(
        time=args.time,
        time_note=args.time_note,
        lat=args.lat,
        lon=args.lon,
        location_note=args.location_note,
        persons=args.persons,
        event=args.event,
        priority=args.priority,
        remark=args.remark,
    )
    return [store.get_event(event_id)]


def update_event(store: EventStore, args: Namespace):
    """更新事件并返回更新后的记录。"""
    payload = {}
    for key in ("time", "time_note", "lat", "lon", "location_note", "persons", "event", "priority", "remark"):
        value = getattr(args, key)
        if value is not None:
            payload[key] = value
    updated = store.update_event(args.id, **payload)
    if updated == 0:
        return []
    return [store.get_event(args.id)]


def get_event(store: EventStore, args: Namespace):
    """获取单条事件。"""
    return [store.get_event(args.id)]


def delete_event(store: EventStore, args: Namespace) -> None:
    """删除事件。"""
    store.delete_event(args.id, hard=args.hard)


def list_events(store: EventStore, args: Namespace):
    """列出事件。"""
    return store.list_events(limit=args.limit, offset=args.offset, order=args.order)


def search_events(store: EventStore, args: Namespace):
    """按条件检索事件。"""
    return store.search_events(
        start_year=args.start_year,
        end_year=args.end_year,
        lat_range=args.lat_range,
        lon_range=args.lon_range,
        person_contains=args.person,
        event_contains=args.event_contains,
        location_contains=args.location_contains,
        priority=args.priority,
        limit=args.limit,
        offset=args.offset,
        order=args.order,
    )
