import unittest
from unittest.mock import patch

from panther_ai.engine import Engine
from panther_ai.tools import TOOL_REGISTRY, run_tool


class ToolTests(unittest.TestCase):
    def test_registry_has_safe_read_tools(self):
        self.assertEqual(set(TOOL_REGISTRY), {"system_info", "disk_usage", "docker_ps"})
        self.assertTrue(all(item["risk"] == "read" for item in TOOL_REGISTRY.values()))

    def test_system_info(self):
        result = run_tool("system_info", {})
        self.assertIn("hostname", result)
        self.assertIn("kernel", result)
        self.assertIn("cpu_count", result)

    def test_disk_usage(self):
        result = run_tool("disk_usage", {"path": "/"})
        self.assertEqual(result["path"], "/")
        self.assertGreater(result["usage"]["total"], 0)


class EngineTests(unittest.TestCase):
    def test_docker_prompt_selects_tool(self):
        engine = Engine()
        with patch.object(engine.runtime, "generate", return_value="ignored") as generate:
            with patch("panther_ai.engine.run_tool", return_value={"containers": []}) as tool:
                result = engine.chat("ما حالة Docker عندي؟")
        self.assertEqual(result["tool"], "docker_ps")
        tool.assert_called_once_with("docker_ps", {})
        generate.assert_called_once()
        self.assertIn("Docker", result["answer"])

    def test_refusal_is_replaced_by_grounded_answer(self):
        engine = Engine()
        with patch.object(engine.runtime, "generate", return_value="لا يمكنني الوصول إلى الجهاز"):
            with patch("panther_ai.engine.run_tool", return_value={
                "containers": [
                    {"name": "portainer", "image": "portainer/portainer-ce:latest", "status": "Up"}
                ]
            }):
                result = engine.chat("docker")
        self.assertIn("portainer", result["answer"])
        self.assertNotIn("لا يمكنني", result["answer"])


if __name__ == "__main__":
    unittest.main()
