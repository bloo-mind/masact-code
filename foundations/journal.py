"""The journal is the truth: an append-only log; state is a fold of it.

Event sourcing. Persistence, crash-resumption, and deterministic replay
all fall out of this one decision as corollaries. Chapter 20 prints
``append``, ``events``, and ``fold``.
"""

import json
import time


def append(path: str, kind: str, **data) -> dict:
    event = {"v": 1, "t": time.time(), "kind": kind, **data}
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")
    return event


def events(path: str) -> list[dict]:
    out: list[dict] = []
    with open(path) as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:  # a torn final line: died mid-write
                break
    return out


def fold(evts: list[dict]) -> dict:
    """The reducer: state is a view, recomputable at will."""
    state = {"spent": 0, "finished": [], "messages": 0}
    for e in evts:
        match e["kind"]:
            case "BudgetDebited":
                state["spent"] += e["amount"]
            case "AgentFinished":
                state["finished"].append(e["agent"])
            case "MessageDelivered":
                state["messages"] += 1
            # ...one arm per event kind the views care about
    return state
