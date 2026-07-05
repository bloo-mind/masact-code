"""The foundations layer: the from-scratch runtime of *Multi-Agent Systems: A
Contemporary Treatment*, plus small, transparent implementations of the
classical algorithms the book discusses.

Everything here runs on the Python standard library alone. The runtime
modules (``model``, ``tools``, ``context``, ``journal``, ``messages``,
``mailbox``, ``budget``, ``agent``, ``team``) are the ones Chapter 20
builds; the ``algorithms`` and ``emergence`` subpackages carry the
classics named across the rest of the book.
"""

from .agent import run
from .budget import Budget
from .context import assemble
from .journal import append, events, fold
from .mailbox import Mailbox
from .messages import Message, Performative
from .model import FakeClient, ModelClient, ModelResponse, ToolCall
from .team import Worker, integrate, run_team
from .tools import Tool, dispatch

__all__ = [
    "run", "Budget", "assemble", "append", "events", "fold", "Mailbox",
    "Message", "Performative", "FakeClient", "ModelClient", "ModelResponse",
    "ToolCall", "Worker", "integrate", "run_team", "Tool", "dispatch",
]
