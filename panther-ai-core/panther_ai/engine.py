import json

from .memory import Memory
from .runtime import Runtime
from .tools import TOOL_REGISTRY, run_tool


class Engine:
    def __init__(self):
        self.memory = Memory()
        self.runtime = Runtime()
        self.max_tool_steps = 3

    def _select_tools(self, prompt: str):
        text = prompt.lower()
        tools = []
        if any(w in text for w in ("docker", "كونتينر", "حاوية")):
            tools.append(("docker_ps", {}))
        if any(w in text for w in ("disk", "storage", "filesystem", "قرص", "تخزين", "مساحة")):
            tools.append(("disk_usage", {"path": "/"}))
        if any(w in text for w in ("system", "hostname", "kernel", "cpu", "جهاز", "نظام", "معالج")):
            tools.append(("system_info", {}))
        return tools[:self.max_tool_steps]

    def _run_tool(self, name, args):
        meta = TOOL_REGISTRY.get(name)
        if not meta or meta.get("risk") != "read":
            raise PermissionError("Tool is not authorized")
        return run_tool(name, args)

    def chat(self, prompt: str):
        context = self.memory.context()
        executed = []
        for name, args in self._select_tools(prompt):
            try:
                result = self._run_tool(name, args)
            except Exception as exc:
                result = {"error": str(exc)}
            executed.append({"name": name, "result": result})
            context += "\n\nTool result (real local data):\n" + json.dumps(result, ensure_ascii=False)

        try:
            answer = self.runtime.generate(prompt, context)
        except Exception as exc:
            answer = f"Local model unavailable: {exc}"

        self.memory.add("user", prompt)
        self.memory.add("assistant", answer)
        response = {"answer": answer}
        if executed:
            response["tools"] = executed
        return response
