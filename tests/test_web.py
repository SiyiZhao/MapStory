import tempfile
import unittest
from pathlib import Path

from mapstory.ext import create_app


class WebUITests(unittest.TestCase):
    """Web UI 回归测试。"""

    def setUp(self) -> None:
        """创建临时数据库和测试客户端。"""
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "web.db"
        self.app = create_app(self.db_path, test_config={"TESTING": True})
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        """清理数据库文件。"""
        self._tmp.cleanup()

    def test_list_page_renders_empty_state(self) -> None:
        """验证列表页可渲染且显示空状态。"""
        response = self.client.get("/events")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("MapStory Web UI", body)
        self.assertIn("当前没有匹配的事件", body)

    def test_list_page_handles_negative_year(self) -> None:
        """验证古代年份不会让列表页崩溃。"""
        create_response = self.client.post(
            "/api/events",
            json={
                "event": "秦始皇三十六年巡游",
                "time_iso": "-221",
                "priority": "fact",
            },
        )
        self.assertEqual(create_response.status_code, 201)

        response = self.client.get("/events")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("-221", body)
        self.assertIn("秦始皇三十六年巡游", body)

    def test_api_create_list_update_and_delete(self) -> None:
        """验证事件 API 的增删改查流程。"""
        create_response = self.client.post(
            "/api/events",
            json={
                "event": "辛亥首义",
                "time_iso": "1911-10-10",
                "lat": 30.6,
                "lon": 114.3,
                "location_note": "武昌",
                "persons": ["新军"],
                "priority": "fact",
                "remark": "test",
            },
        )
        self.assertEqual(create_response.status_code, 201)
        created = create_response.get_json()["data"]
        self.assertEqual(created["event"], "辛亥首义")

        list_response = self.client.get("/api/events")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.get_json()["data"]), 1)

        patch_response = self.client.patch(f"/api/events/{created['id']}", json={"remark": "updated"})
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.get_json()["data"]["remark"], "updated")

        delete_response = self.client.delete(f"/api/events/{created['id']}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(delete_response.get_json()["data"]["deleted"])

    def test_form_create_redirects_to_detail(self) -> None:
        """验证 HTML 表单可创建事件并跳转详情页。"""
        response = self.client.post(
            "/events/new",
            data={
                "event": "页面新增",
                "time_iso": "2024-01-15",
                "persons": "张三, 李四",
                "priority": "doubt",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        location = response.headers["Location"]
        detail_response = self.client.get(location)
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn("页面新增", detail_response.get_data(as_text=True))

    def test_list_page_location_filter(self) -> None:
        """验证列表页支持按地点备注筛选。"""
        self.client.post(
            "/api/events",
            json={
                "event": "武昌起义",
                "time_iso": "1911-10-10",
                "location_note": "武昌",
                "priority": "fact",
            },
        )
        self.client.post(
            "/api/events",
            json={
                "event": "上海开埠",
                "time_iso": "1843-11-17",
                "location_note": "上海",
                "priority": "fact",
            },
        )

        response = self.client.get("/events?location=武昌")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("武昌起义", body)
        self.assertNotIn("上海开埠", body)

    def test_detail_page_uses_remark_source_section(self) -> None:
        """验证详情页下方展示“备注 / 来源”而非“事件内容”。"""
        create_response = self.client.post(
            "/api/events",
            json={
                "event": "长平之战",
                "time_iso": "-260",
                "priority": "fact",
                "remark": "《史记》卷七十三",
            },
        )
        self.assertEqual(create_response.status_code, 201)
        event_id = create_response.get_json()["data"]["id"]

        response = self.client.get(f"/events/{event_id}")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("备注 / 来源", body)
        self.assertIn("《史记》卷七十三", body)
        self.assertNotIn("事件内容", body)


if __name__ == "__main__":
    unittest.main()