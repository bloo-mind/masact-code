"""Typed, performative messages: speech acts as an enum.

The performative is Searle's taxonomy on the wire; a mailbox and a schema
beat a group chat, and the margin is widest when things go wrong. Chapter
20 prints ``Performative`` and ``Message``.
"""

from dataclasses import dataclass
from enum import Enum


class Performative(Enum):
    REQUEST = "request"
    INFORM = "inform"
    PROPOSE = "propose"
    ACCEPT = "accept"
    REJECT = "reject"
    DONE = "done"
    ERROR = "error"


@dataclass
class Message:
    performative: Performative
    sender: str
    recipient: str
    task_id: str
    payload: dict
