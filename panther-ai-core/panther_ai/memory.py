import json
from pathlib import Path

class Memory:
    def __init__(self, path="~/.panther-ai/memory.json"):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self):
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def add(self, role, content):
        self.data.append({"role": role, "content": content})
        self.path.write_text(json.dumps(self.data[-200:], ensure_ascii=False, indent=2))

    def context(self, limit=20):
        return "\n".join(f"{x['role']}: {x['content']}" for x in self.data[-limit:])
