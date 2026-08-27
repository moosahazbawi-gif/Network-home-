import json
import os
import urllib.request

class LocalModel:
    """Adapter for a local Ollama-compatible HTTP endpoint. No cloud service required."""
    def __init__(self, base_url=None, model=None):
        self.base_url = (base_url or os.getenv("PANTHER_LLM_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("PANTHER_LLM_MODEL", "llama3.2:3b")

    def generate(self, prompt: str, context: str = "") -> str:
        payload = json.dumps({"model": self.model, "prompt": f"Context:\n{context}\n\nUser:\n{prompt}", "stream": False}).encode()
        req = urllib.request.Request(self.base_url + "/api/generate", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read()).get("response", "")
