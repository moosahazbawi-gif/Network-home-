import json
import os
import urllib.request

class LocalModel:
    """Local llama.cpp model adapter. No cloud service required."""

    def __init__(self, base_url=None, model=None):
        self.base_url = (
            base_url or os.getenv("PANTHER_LLM_URL", "http://127.0.0.1:11434")
        ).rstrip("/")
        self.model = model or os.getenv(
            "PANTHER_LLM_MODEL",
            "qwen2.5-1.5b-instruct-q4_k_m.gguf"
        )

    def generate(self, prompt: str, context: str = "") -> str:
        full_prompt = f"""أنت Panther AI، نظام ذكاء اصطناعي محلي يعمل على هذا الجهاز.
أجب باللغة التي يستخدمها المستخدم.
كن واضحًا ومباشرًا.

السياق:
{context}

تعليمات مهمة:
إذا كان السياق يحتوي على "Tool result"، فهذه نتيجة حقيقية تم الحصول عليها من الجهاز.
استخدمها للإجابة عن سؤال المستخدم ولا تدّعي عدم القدرة على الوصول إلى الجهاز.
لا تخترع معلومات غير موجودة في نتيجة الأداة.

المستخدم:
{prompt}
"""

        payload = json.dumps({
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            "stream": False
        }).encode()

        req = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read())

        return data["choices"][0]["message"]["content"]
