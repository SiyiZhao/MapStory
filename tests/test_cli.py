import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from mapstory.cli import build_parser, dispatch


class CLITests(unittest.TestCase):
    """CLI 参数解析与分发测试。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "cli.db"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_parser_accepts_time_argument(self) -> None:
        """验证 CLI 支持 --time 参数并能正确解析。"""
        parser = build_parser()
        args = parser.parse_args(
            [
                "--db",
                str(self.db_path),
                "event",
                "create",
                "--event",
                "测试事件",
                "--time",
                "1911-10-10 18:30",
                "--time-note",
                "宣统三年",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.time, "1911-10-10 18:30")
        self.assertEqual(args.time_note, "宣统三年")

    def test_dispatch_create_and_get_roundtrip(self) -> None:
        """验证 dispatch 可完成创建并读取事件。"""
        parser = build_parser()
        create_args = parser.parse_args(
            [
                "--db",
                str(self.db_path),
                "event",
                "create",
                "--event",
                "武昌起义",
                "--time",
                "1911-10-10",
                "--time-note",
                "宣统三年",
                "--format",
                "json",
            ]
        )

        create_stdout = io.StringIO()
        with redirect_stdout(create_stdout):
            dispatch(create_args)
        create_output = create_stdout.getvalue()
        self.assertIn('"time": "1911-10-10"', create_output)
        self.assertIn('"time_note": "宣统三年"', create_output)

        get_args = parser.parse_args(
            [
                "--db",
                str(self.db_path),
                "event",
                "get",
                "1",
                "--format",
                "json",
            ]
        )

        get_stdout = io.StringIO()
        with redirect_stdout(get_stdout):
            dispatch(get_args)
        get_output = get_stdout.getvalue()
        self.assertIn('"event": "武昌起义"', get_output)
        self.assertIn('"time": "1911-10-10"', get_output)


if __name__ == "__main__":
    unittest.main()
