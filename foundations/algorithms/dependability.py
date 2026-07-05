"""Dependability cores for agent systems (Chapter 23).

Two of the chapter's plain-Python mechanisms, each reproduced verbatim so
that a reader copying from the book finds the identical function here.

``deliver`` is the retry-with-backoff wrapper guarded by an idempotency
key: a transient *Heisenbug* is retried after an exponential backoff with
jitter, while a repeated request for a key already spent is served from the
``seen`` cache rather than run a second time --- reads retry freely, but an
irreversible effect is keyed and never re-executed on a duplicate delivery.

``run_to_gate`` / ``approve`` are the human gate as persistence, not a
dialogue box: reaching the gate appends an ``ApprovalRequested`` event and
returns ``"parked"`` (the process stops existing); the later ``approve``
appends ``ApprovalGranted`` and folds the run forward from the same cut. A
park lasting ten seconds or ten days is the same fold, resumed later.

Standard library only; the Chapter 20 runtime is not imported. The backoff
sleeps are real (``0.2 * 2**k`` seconds plus jitter); the jitter sizes a
delay only and never changes an outcome, so tests stay deterministic by
monkeypatching ``time.sleep`` to a no-op. The module-level ``seen``,
``faults`` and ``journal`` are the book's demonstration state; the tests
reset them per case.
"""

import random
import time
from collections.abc import Callable

__all__ = [
    "seen",
    "faults",
    "charge_card",
    "deliver",
    "journal",
    "run_to_gate",
    "approve",
]

# --- Retry, backoff, idempotency key (verbatim from Chapter 23) ------------

seen: dict[str, str] = {}                  # the idempotency-key cache
faults = [TimeoutError("gateway slow")]    # one transient Heisenbug


def charge_card() -> str:                  # each call: one ToolDispatched
    if faults:
        raise faults.pop()
    return "charged 1500p"


def deliver(key: str, fn: Callable[[], str], n: int = 3) -> str:
    for k in range(n):
        try:                               # success: ToolReturned, cached
            return seen[key] if key in seen else seen.setdefault(key, fn())
        except TimeoutError:               # transient: back off with jitter
            time.sleep(0.2 * 2**k + random.uniform(0, 0.2))
    raise TimeoutError(f"retries exhausted: {key}")


# --- The human gate over a list-of-events journal (verbatim, Chapter 23) ---

journal: list[tuple[str, str]] = []    # (event, action) pairs, append-only


def run_to_gate(action: str) -> str:
    granted = ("ApprovalGranted", action) in journal  # a fold over events
    if not granted:
        journal.append(("ApprovalRequested", action))
        return "parked"
    return f"deployed {action}"        # past the gate, the effect fires


def approve(action: str) -> str:
    journal.append(("ApprovalGranted", action))
    return run_to_gate(action)
