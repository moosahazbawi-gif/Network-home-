from .model import RuleModel
from .memory import Memory

class Planner:
    def __init__(self, model=None, memory=None):
        self.model = model or RuleModel()
        self.memory = memory or Memory()

    def run(self, prompt: str):
        context = self.memory.context()
        answer = self.model.generate(prompt, context)
        self.memory.add("user", prompt)
        self.memory.add("assistant", answer)
        return {"answer": answer}
