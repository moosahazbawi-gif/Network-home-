from .memory import Memory
from .runtime import Runtime

class Engine:
    def __init__(self):
        self.memory = Memory()
        self.runtime = Runtime()

    def chat(self, prompt: str):
        context = self.memory.context()
        try:
            answer = self.runtime.generate(prompt, context)
        except Exception as exc:
            answer = f"Local model unavailable: {exc}"
        self.memory.add("user", prompt)
        self.memory.add("assistant", answer)
        return {"answer": answer}
