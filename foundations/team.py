"""The coordinating harness: the Contract Net, minus the bidding.

The orchestrator is just another agent whose tools operate on the team ---
decompose, dispatch, collect, verify, integrate. ``integrate`` (printed in
Chapter 20) is the whole difference between a reviewer *role* and a reviewer
*costume*: it will not merge without a prior ``ACCEPT`` on the task thread.
"""

from dataclasses import dataclass, field
from typing import Callable

from .agent import run
from .budget import Budget
from .mailbox import Mailbox
from .messages import Message, Performative
from .model import ModelClient
from .tools import Tool


def integrate(inbox: list[Message], task_id: str,
              apply: Callable[[], object]):
    approvals = [m for m in inbox
                 if m.task_id == task_id
                 and m.performative is Performative.ACCEPT]
    if not approvals:
        raise PermissionError(f"no ACCEPT on task {task_id}: not merging")
    return apply()


@dataclass
class Worker:
    """A role: a client, its toolset, and its standing instructions."""

    role: str
    client: ModelClient
    system: str
    tools: list[Tool] = field(default_factory=list)


def run_team(task: str, coder: Worker, reviewer: Worker, tester: Worker,
             journal_path: str, budget: Budget) -> dict:
    """Dispatch the task to the coder, gate the merge on the reviewer's
    ``ACCEPT``, and let the tester confirm the integrated result. The
    reviewer and tester report a verdict in their ``done`` payload under
    the key ``verdict`` (``"accept"`` / ``"reject"`` / ``"green"``)."""
    box = Mailbox(journal_path)
    task_id = "T1"

    box.send(Message(Performative.REQUEST, "orchestrator", coder.role,
                     task_id, {"task": task}))
    made = run(coder.role, coder.client, coder.tools, coder.system,
               task, journal_path, budget)
    if made.get("status") != "done":
        return {"status": "no-merge", "reason": made.get("status")}
    box.send(Message(Performative.DONE, coder.role, "orchestrator",
                     task_id, made))

    seen = run(reviewer.role, reviewer.client, reviewer.tools,
               reviewer.system, str(made), journal_path, budget)
    verdict = seen.get("verdict") == "accept"
    box.send(Message(Performative.ACCEPT if verdict else Performative.REJECT,
                     reviewer.role, "orchestrator", task_id, {}))

    try:
        merged = integrate(box.drain("orchestrator"), task_id,
                           lambda: made)
    except PermissionError as exc:
        return {"status": "rejected", "reason": str(exc)}

    checked = run(tester.role, tester.client, tester.tools, tester.system,
                  str(merged), journal_path, budget)
    return {"status": "shipped", "result": merged,
            "suite": checked.get("verdict")}
