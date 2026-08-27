from .local_model import LocalModel

class Runtime:
    def __init__(self):
        self.model = LocalModel()

    def generate(self, prompt, context=""):
        return self.model.generate(prompt, context)
