import tempfile
import unittest
from pathlib import Path

from mapstory.import_ import ZHANG_LIANG_LIUHOU_EVENTS, seed_zhang_liang_liuhou_events
from mapstory.store import EventStore


class LiuhouSeedTests(unittest.TestCase):
    """《留侯世家》事件种子回归测试。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = EventStore(Path(self._tmp.name) / "liuhou.db")

    def tearDown(self) -> None:
        self.store.conn.close()
        self._tmp.cleanup()

    def test_seed_creates_zhang_liang_events_once(self) -> None:
        created = seed_zhang_liang_liuhou_events(self.store)
        created_again = seed_zhang_liang_liuhou_events(self.store)
        rows = self.store.search_events(person_contains="张良", limit=200, order="time")

        self.assertEqual(len(created), len(ZHANG_LIANG_LIUHOU_EVENTS))
        self.assertEqual(created_again, [])
        self.assertEqual(len(rows), len(ZHANG_LIANG_LIUHOU_EVENTS))
        self.assertEqual(rows[0]["location_note"], "韩国新郑（今河南新郑）")
        self.assertEqual(rows[-1]["event"], "张良卒，谥文成侯；其后与黄石信仰一并祭祀。")


if __name__ == "__main__":
    unittest.main()
