from panther_ai.tools import TOOL_REGISTRY, run_tool


def test_tool_registry_contains_read_tools():
    assert {"system_info", "disk_usage", "docker_ps"} <= set(TOOL_REGISTRY)


def test_system_info_returns_host_data():
    result = run_tool("system_info", {})
    assert result["hostname"]
    assert result["kernel"]
    assert result["cpu_count"] > 0


def test_disk_usage_returns_expected_shape():
    result = run_tool("disk_usage", {"path": "/"})
    assert result["path"] == "/"
    assert set(result["usage"]) >= {"total", "used", "free"}
