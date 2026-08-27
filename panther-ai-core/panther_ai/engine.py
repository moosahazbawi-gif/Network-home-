import json

from .memory import Memory
from .runtime import Runtime
from .tools import run_tool


class Engine:
    def __init__(self):
        self.memory = Memory()
        self.runtime = Runtime()

    def _select_tool(self, prompt: str):
        text = prompt.lower()
        if any(word in text for word in ("docker", "كونتينر", "حاوية")):
            return "docker_ps", {}
        if any(word in text for word in ("disk", "storage", "filesystem", "قرص", "تخزين", "مساحة")):
            return "disk_usage", {"path": "/"}
        if any(word in text for word in ("system", "hostname", "kernel", "cpu", "جهاز", "نظام", "معالج")):
            return "system_info", {}
        return None, None

    def chat(self, prompt: str):
        context = self.memory.context()
        tool_name, tool_args = self._select_tool(prompt)
        tool_result = None

        if tool_name:
            try:
                tool_result = run_tool(tool_name, tool_args)
            except Exception as exc:
                tool_result = {"error": str(exc)}

        if tool_result is not None:
            context = f"{context}\n\nTool used: {tool_name}\nTool result:\n{json.dumps(tool_result, ensure_ascii=False)}"

        try:
            answer = self.runtime.generate(prompt, context)
        except Exception as exc:
            answer = f"Local model unavailable: {exc}"

        self.memory.add("user", prompt)
        self.memory.add("assistant", answer)
        return {"answer": answer, "tool": tool_name}
