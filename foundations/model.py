"""The model boundary: everything vendor-specific behind one method.

Chapter 20 prints the body of this module (from ``ModelResponse`` on) as
an excerpt.
"""

from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    args: dict


@dataclass
class ModelResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: int = 0                     # tokens this call cost, always


class ModelClient:
    """One method; everything vendor-specific lives behind it."""

    def complete(self, messages: list[dict],
                 tools: list[dict]) -> ModelResponse:
        raise NotImplementedError


class FakeClient(ModelClient):
    """Replays a script: deterministic tests, no tokens spent."""

    def __init__(self, script: list[ModelResponse]):
        self.script = list(script)

    def complete(self, messages, tools):
        return self.script.pop(0)
