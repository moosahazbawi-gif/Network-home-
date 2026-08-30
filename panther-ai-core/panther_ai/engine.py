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
        if any(word in text for word in ("docker", "container", "containers", "كونتينر", "حاوية", "حاويات")):
            return "docker_ps", {}
        if any(word in text for word in ("disk", "storage", "filesystem", "space", "قرص", "تخزين", "ملفات", "مساحة")):
            return "disk_usage", {"path": "/"}
        if any(word in text for word in ("system", "hostname", "kernel", "cpu", "machine", "جهاز", "نظام", "معالج")):
            return "system_info", {}
        return None, None

    def _grounded_fallback(self, tool_name, result):
        if not isinstance(result, dict):
            return None
        if "error" in result:
            return f"تعذر تنفيذ الأداة {tool_name}: {result['error']}"
        if tool_name == "docker_ps":
            containers = result.get("containers", [])
            if not containers:
                return "Docker يعمل، ولا توجد حاويات قيد التشغيل حاليًا."
            lines = [f"Docker يعمل حاليًا، والحاويات قيد التشغيل: {len(containers)}."]
            for item in containers:
                lines.append(f"- {item.get('name', '?')} — {item.get('image', '?')} — {item.get('status', '?')}")
            return "\n".join(lines)
        if tool_name == "system_info":
            return (
                f"الجهاز: {result.get('hostname')}، النظام: {result.get('os')}، "
                f"النواة: {result.get('kernel')}، المعالجات: {result.get('cpu_count')}."
            )
        if tool_name == "disk_usage":
            usage = result.get("usage", {})
            total = usage.get("total", 0)
            used = usage.get("used", 0)
            free = usage.get("free", 0)
            return f"مساحة {result.get('path', '/')} — الإجمالي: {total} بايت، المستخدم: {used} بايت، المتاح: {free} بايت."
        return None

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
            context = (
                f"{context}\n\nTool used: {tool_name}\n"
                f"Tool result (authoritative host data):\n"
                f"{json.dumps(tool_result, ensure_ascii=False)}"
            )

        try:
            answer = self.runtime.generate(prompt, context)
        except Exception as exc:
            answer = f"Local model unavailable: {exc}"

        if tool_result is not None:
            refusal_markers = (
                "لا أستطيع", "ليس لدي القدرة", "لا يمكنني", "لا أملك القدرة",
                "أعتذر", "cannot", "unable", "don't have access", "do not have access"
            )
            if any(marker in answer.lower() for marker in refusal_markers):
                fallback = self._grounded_fallback(tool_name, tool_result)
                if fallback:
                    answer = fallback

        self.memory.add("user", prompt)
        self.memory.add("assistant", answer)
        return {"answer": answer, "tool": tool_name}
