import tempfile
import unittest
from pathlib import Path

from mapstory import EventStore, InputValidationError


class StageATests(unittest.TestCase):
    def setUp(self) -> None:
        """为每个测试创建独立临时数据库，避免用例间互相污染。"""
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "test.db"
        self.store = EventStore(self.db_path)

    def tearDown(self) -> None:
        """关闭数据库连接并清理临时目录。"""
        self.store.conn.close()
        self._tmp.cleanup()

    def test_create_validates_required_event(self) -> None:
        """验证新增事件时 event 为空白字符串会触发 InputValidationError。"""
        with self.assertRaises(InputValidationError):
            self.store.create(
                time="2020-01-01",
                time_note=None,
                lat=None,
                lon=None,
                location_note=None,
                persons=None,
                event="   ",
                priority="fact",
                remark=None,
            )

    def test_create_validates_coordinates(self) -> None:
        """验证纬度超出 [-90, 90] 范围时会被拒绝。"""
        with self.assertRaises(InputValidationError):
            self.store.create(
                time="2020-01-01",
                time_note=None,
                lat=91.0,
                lon=0.0,
                location_note="x",
                persons="a",
                event="invalid lat",
                priority="fact",
                remark=None,
            )

    def test_time_sorting_handles_precision_and_empty(self) -> None:
        """验证 list_all 按时间和精度排序：年 > 日 > 空值。"""
        self.store.create(
            time="2020-05-01",
            time_note=None,
            lat=None,
            lon=None,
            location_note=None,
            persons=None,
            event="precise",
            priority="fact",
            remark=None,
        )
        self.store.create(
            time="2020",
            time_note=None,
            lat=None,
            lon=None,
            location_note=None,
            persons=None,
            event="fuzzy",
            priority="fact",
            remark=None,
        )
        self.store.create(
            time=None,
            time_note="二十六年",
            lat=None,
            lon=None,
            location_note=None,
            persons=None,
            event="conflict",
            priority="fact",
            remark=None,
        )
        self.store.create(
            time=None,
            time_note=None,
            lat=None,
            lon=None,
            location_note=None,
            persons=None,
            event="empty",
            priority="fact",
            remark=None,
        )

        rows = self.store.list_all(sort_by="time", limit=10)
        self.assertEqual([row["event"] for row in rows], ["fuzzy", "precise", "empty", "conflict"])

    def test_update_recomputes_time_fields(self) -> None:
        """验证 update 修改 time 后会重算 time_year/month/day/hour/minute。"""
        event_id = self.store.create(
            time=None,
            time_note=None,
            lat=None,
            lon=None,
            location_note=None,
            persons=None,
            event="to-update",
            priority="fact",
            remark=None,
        )

        self.store.update(event_id, time="1999-12-31 08")
        row = self.store.conn.execute(
            "SELECT time_year, time_month, time_day, time_hour, time_minute FROM events WHERE id = ?",
            (event_id,),
        ).fetchone()

        self.assertEqual(row["time_year"], 1999)
        self.assertEqual(row["time_month"], 12)
        self.assertEqual(row["time_day"], 31)
        self.assertEqual(row["time_hour"], 8)
        self.assertIsNone(row["time_minute"])

    def test_filter_supports_normalized_ranges(self) -> None:
        """验证检索时反向区间输入会自动归一化后正确命中事件。"""
        self.store.create(
            time="1911-10-10",
            time_note=None,
            lat=30.6,
            lon=114.3,
            location_note="武昌",
            persons="新军",
            event="起义",
            priority="fact",
            remark=None,
        )

        rows = self.store.filter(
            {
                "lat_range": (40.0, 20.0),
                "lon_range": (120.0, 100.0),
            }
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event"], "起义")


if __name__ == "__main__":
    unittest.main()
