from typing import Protocol

class Model(Protocol):
    def generate(self, prompt: str, context: str = "") -> str: ...

class RuleModel:
    """Deterministic bootstrap model; replaceable by a local LLM adapter."""
    def generate(self, prompt: str, context: str = "") -> str:
        return f"Panther received: {prompt}\nContext: {context}" if context else f"Panther received: {prompt}"
