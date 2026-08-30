import json

from .memory import Memory
from .runtime import Runtime
from .tools import TOOL_REGISTRY, run_tool


class Engine:
    def __init__(self):
        self.memory = Memory()
        self.runtime = Runtime()
        self.max_tool_steps = 3

    def _select_tool(self, prompt: str):
        text = prompt.lower()
        if any(w in text for w in ("docker", "كونتينر", "حاوية")):
            return "docker_ps", {}
        if any(w in text for w in ("disk", "storage", "filesystem", "قرص", "تخزين", "مساحة")):
            return "disk_usage", {"path": "/"}
        if any(w in text for w in ("system", "hostname", "kernel", "cpu", "جهاز", "نظام", "معالج")):
            return "system_info", {}
        return None, None

    def _run_tool(self, name, args):
        if name not in TOOL_REGISTRY:
            raise ValueError("Tool is not authorized")
        return run_tool(name, args)

    def chat(self, prompt: str):
        context = self.memory.context()
        tool_name = None
        tool_result = None
        for _ in range(self.max_tool_steps):
            candidate, args = self._select_tool(prompt)
            if not candidate or candidate == tool_name:
                break
            tool_name = candidate
            try:
                tool_result = self._run_tool(tool_name, args)
                context += "\n\nTool result:\n" + json.dumps(tool_result, ensure_ascii=False)
            except Exception as exc:
                tool_result = {"error": str(exc)}
                context += "\n\nTool result:\n" + json.dumps(tool_result, ensure_ascii=False)
            break

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
