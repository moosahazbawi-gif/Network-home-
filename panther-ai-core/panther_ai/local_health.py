import json
import urllib.request

def ollama_available(base_url="http://127.0.0.1:11434"):
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/api/tags", timeout=3) as r:
            return json.loads(r.read())
    except Exception as exc:
        return {"available": False, "error": str(exc)}
