"""Delivery, deliberately dull: an inbox per agent, all journalled."""

from .journal import append
from .messages import Message


class Mailbox:
    def __init__(self, journal_path: str):
        self.journal_path = journal_path
        self.queues: dict[str, list[Message]] = {}

    def send(self, msg: Message) -> None:
        append(self.journal_path, "MessageSent", sender=msg.sender,
               recipient=msg.recipient, task_id=msg.task_id,
               performative=msg.performative.value)
        self.queues.setdefault(msg.recipient, []).append(msg)
        append(self.journal_path, "MessageDelivered",
               recipient=msg.recipient, task_id=msg.task_id)

    def drain(self, agent_id: str) -> list[Message]:
        return self.queues.pop(agent_id, [])
