import json

from .memory import Memory
from .runtime import Runtime
from .tools import TOOL_REGISTRY, run_tool


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
                context += "\n\nTool result:\n" + json.dumps(tool_result, ensure_ascii=False)
            except Exception as exc:
                tool_result = {"error": str(exc)}
                context += "\n\nTool result:\n" + json.dumps(tool_result, ensure_ascii=False)

        try:
            answer = self.runtime.generate(prompt, context)
        except Exception as exc:
            answer = f"Local model unavailable: {exc}"

        self.memory.add("user", prompt)
        self.memory.add("assistant", answer)
        response = {"answer": answer}
        if tool_name:
            response["tool"] = tool_name
            response["tool_result"] = tool_result
        return response
