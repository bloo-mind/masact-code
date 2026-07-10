"""The interop-failure lab (Section 22.5): supervisor meets supervisor.

Two systems, each built around a supervisor that expects to *lead*. Bring
them together and each addresses the other as its subagent, delegates the
task downward, and waits for the other's report. Every message is
schema-valid and well-formed; the envelopes are perfect. And the joint
system makes no progress, because a protocol validates *form*, not the
*architectural* question of who is in charge --- which neither side will
concede.

This is a minimal, honest simulation: a bounded exchange in which the
schemas stay green while the task stays dead. The lesson is not that the
messages are malformed --- they are flawless --- but that no message could
have settled the disagreement.

To prove the deadlock is the leadership *clash* and not a rigged progress
scan, the lab also runs a positive control: :func:`leader_follower_handoff`,
in which one side plays a *follower* policy that concedes the lead and
*submits*. The message schema is identical; the only difference is who
agrees to be led --- and that scenario progresses.
"""

from __future__ import annotations

from collections.abc import Callable

# The two required fields of the shared message schema. A record is
# schema-valid iff both are present and well-typed.
_SCHEMA_FIELDS = ("role", "act")

# The vocabulary a *leader* supervisor is willing to speak: it delegates
# downward and awaits a report upward. It never *submits*.
_LEADER_ACTS = frozenset({"delegate", "await_report"})

# The single act that advances the task: someone submits to the other's
# lead. A pair of leaders never emits it; a follower does.
_PROGRESS_ACT = "submit"

# A policy maps (me, you, turn) to that supervisor's messages for the turn.
Policy = Callable[[str, str, int], list[dict]]


def _schema_valid(msg: dict) -> bool:
    """A record is valid iff every schema field is present and a string."""
    return all(isinstance(msg.get(f), str) for f in _SCHEMA_FIELDS)


def _made_progress(messages: list[dict]) -> bool:
    """Progress requires someone to *submit* to the other's lead."""
    return any(m["act"] == _PROGRESS_ACT for m in messages)


def _leader_turn(me: str, you: str, turn: int) -> list[dict]:
    """A leader's turn: delegate downward, then await a report --- and
    never submit. Two leaders playing this policy deadlock."""
    return [
        # "You are my subagent; take this task."
        {
            "role": "supervisor", "act": "delegate",
            "from": me, "to": you, "turn": turn,
            "auth": f"sig:{me}", "body": "you are my subagent: proceed",
        },
        # "...and I now await your report." (Which never comes, because a
        # peer leader is doing exactly the same thing.)
        {
            "role": "supervisor", "act": "await_report",
            "from": me, "to": you, "turn": turn,
            "auth": f"sig:{me}", "body": "awaiting your report",
        },
    ]


def _follower_turn(me: str, you: str, turn: int) -> list[dict]:
    """A follower's turn: concede the lead --- acknowledge the peer's
    delegation, then *submit* the work upward. This emits the progress act,
    so any exchange containing a follower advances."""
    return [
        # "Understood --- you lead; I am your subagent."
        {
            "role": "subagent", "act": "acknowledge",
            "from": me, "to": you, "turn": turn,
            "auth": f"sig:{me}", "body": "acknowledged: you lead",
        },
        # "Here is the finished work." --- the one act that advances.
        {
            "role": "subagent", "act": _PROGRESS_ACT,
            "from": me, "to": you, "turn": turn,
            "auth": f"sig:{me}", "body": "submitting the completed task",
        },
    ]


def _run_exchange(
    policy_alpha: Policy, policy_beta: Policy, rounds: int, diagnosis: str,
) -> dict:
    """Run a bounded exchange between two supervisors under their policies.

    Each round, alpha acts under ``policy_alpha`` and beta under
    ``policy_beta``. Schema validity is judged over the messages actually
    exchanged: an empty exchange is *not* vacuously valid.
    """
    messages: list[dict] = []
    for turn in range(rounds):
        messages.extend(policy_alpha("alpha", "beta", turn))
        messages.extend(policy_beta("beta", "alpha", turn))
    all_valid = bool(messages) and all(_schema_valid(m) for m in messages)
    return {
        "messages": messages,
        "all_schema_valid": all_valid,
        "task_progressed": _made_progress(messages),
        "diagnosis": diagnosis,
    }


def supervisor_deadlock(rounds: int = 3) -> dict:
    """Simulate the bounded exchange between two lead supervisors.

    Each round, both supervisors delegate to the other and then wait for a
    report. Every message is schema-valid and well-formed; none is a
    submission. The exchange is bounded, so it terminates --- but with the
    schemas green and the task dead.
    """
    return _run_exchange(
        _leader_turn, _leader_turn, rounds, "schemas green, task dead")


def leader_follower_handoff(rounds: int = 3) -> dict:
    """Positive control: one leader, one follower --- the task progresses.

    Alpha plays the same leader policy as in :func:`supervisor_deadlock`;
    beta concedes the lead and submits. The message schema is identical to
    the deadlock's, so ``all_schema_valid`` is again green --- but because a
    follower emits the progress act, ``task_progressed`` is now True. This
    proves the deadlock is the leadership *clash*, not a rigged scan.
    """
    return _run_exchange(
        _leader_turn, _follower_turn, rounds,
        "schemas green, task progressed")
