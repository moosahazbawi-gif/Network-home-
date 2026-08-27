from .planner import Planner

class Engine:
    def __init__(self):
        self.planner = Planner()

    def chat(self, prompt: str):
        return self.planner.run(prompt)
