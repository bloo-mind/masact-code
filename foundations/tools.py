"""Tools are data; the dispatcher is the deterministic layer that runs them.

A tool's schema is a STRIPS operator in JSON: preconditions (the required
arguments) and an effect (what the callable does). Errors come back as
observations, never as raised exceptions, because the model's next perception
must be something it can read and retry against.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str                  # when to use it, in plain language
    schema: dict                      # the arguments, JSON-Schema-shaped
    fn: Callable[..., object]


def dispatch(tool: Tool, args: dict) -> dict:
    for key in tool.schema.get("required", []):
        if key not in args:
            return {"tool": tool.name, "error": f"missing argument: {key}"}
    try:
        return {"tool": tool.name, "result": tool.fn(**args)}
    except Exception as exc:          # errors are observations
        return {"tool": tool.name,
                "error": f"{type(exc).__name__}: {exc}"}
