from panther_ai.engine import Engine


def test_docker_request_uses_registered_tool(monkeypatch):
    calls = []

    def fake_run_tool(name, args):
        calls.append((name, args))
        return {"containers": [{"name": "portainer", "image": "portainer/portainer-ce:latest", "status": "Up"}]}

    class FakeRuntime:
        def generate(self, prompt, context=""):
            assert "docker_ps" in context
            assert "portainer" in context
            return "Docker يعمل."

    engine = Engine()
    engine.runtime = FakeRuntime()
    monkeypatch.setattr("panther_ai.engine.run_tool", fake_run_tool)

    result = engine.chat("ما حالة Docker عندي؟")

    assert result["tool"] == "docker_ps"
    assert calls == [("docker_ps", {})]
    assert "Docker" in result["answer"]
