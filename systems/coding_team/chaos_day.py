"""Chaos day (Chapter 23, the finale of the assembled system).

Inject the six failures from the chapter's inventory --- a crash, a hang, a
duplicate, a runaway bill, a deploy, and a human breaking in --- against the
one assembled team, and confirm that each is *boring*: six injections, six
one-line entries in the morning log, none of them requiring a human before
nine. A surprise here would be a defect in the machinery, so the script
doubles as an executable assertion that the dependability mechanisms hold.

Every mechanism under test lives elsewhere in this repository in plain,
standard-library Python --- the checkpointer and retry in the graph, the
idempotency key and the treasury in ``foundations/`` --- and chaos day is
where they are assembled and broken on purpose. It runs on a
``ScriptedBrain``: no model, no key, no network, because what is under test is
the harness.

    uv run python -m systems.coding_team.chaos_day
"""

from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from foundations.algorithms import dependability as dep
from foundations.budget import Budget

from .brains import ScriptedBrain
from .graph import build_team
from .state import initial_state

_LOG: list[tuple[str, str]] = []


def _cfg(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _note(injection: str, outcome: str) -> None:
    _LOG.append((injection, outcome))
    print(f"  [{injection:<17}] {outcome}")


def _resume_to_end(app: object, cfg: dict, first: object) -> dict:
    """Answer every human gate with approval until the run finishes."""
    result = first
    while "__interrupt__" in result:
        result = app.invoke(Command(resume=True), cfg)
    return result


# --- 1. The process dies mid-run ------------------------------------------

class _CrashOnce:
    """A ScriptedBrain whose host is rescheduled once, during the review
    turn --- an infrastructure crash, not a bug; the restart behaves."""

    def __init__(self) -> None:
        self._armed = True
        self._inner = ScriptedBrain()

    def code(self, state: dict) -> dict:
        return self._inner.code(state)

    def review(self, state: dict) -> dict:
        if self._armed:
            self._armed = False
            raise RuntimeError("container rescheduled")
        return self._inner.review(state)

    def test(self, state: dict) -> dict:
        return self._inner.test(state)


def crash_mid_run() -> bool:
    saver = InMemorySaver()                   # the durable truth, off-process
    brain = _CrashOnce()
    cfg = _cfg("nightly")
    app = build_team(brain, checkpointer=saver)
    try:
        app.invoke(initial_state("harden the parser"), cfg)
    except RuntimeError:
        pass                                  # the process died mid-review

    # A fresh process reads the same checkpoint and carries on from the cut.
    reborn = build_team(brain, checkpointer=saver)
    survived = reborn.get_state(cfg).values.get("findings", [])
    final = _resume_to_end(reborn, cfg, reborn.invoke(None, cfg))
    boring = final["status"] == "shipped" and len(survived) >= 1
    _note("crash mid-run",
          f"resumed from checkpoint, {len(survived)} turn(s) "
          f"of work intact; shipped={final['status'] == 'shipped'}")
    return boring


# --- 2. The test runner hangs ---------------------------------------------

def test_hangs() -> bool:
    # The tester times out on every attempt; the node's RetryPolicy backs off,
    # exhausts, and the task is shelved to the dead-letter queue with its
    # trace rather than retried into the ground.
    app = build_team(ScriptedBrain(test_faults=99))
    cfg = _cfg("flaky")
    dead_letter: list[tuple[str, str]] = []
    task = "fix the flaky suite"
    try:
        _resume_to_end(app, cfg, app.invoke(initial_state(task), cfg))
    except Exception as exc:                  # retries exhausted: a Bohrbug
        dead_letter.append((task, type(exc).__name__))
    shelved = dead_letter[0][1] if dead_letter else "none"
    _note("test hangs",
          f"retried to the cap, then dead-lettered ({shelved}); "
          f"the run moved on")
    return bool(dead_letter)                  # shelved, not looping forever


# --- 3. A tool result is delivered twice ----------------------------------

def duplicate_tool_result() -> bool:
    dep.seen.clear()
    dep.faults.clear()                        # no transient fault this time
    fired = {"n": 0}

    def merge() -> str:                       # an irreversible effect
        fired["n"] += 1
        return "merged PR #42"

    key = "merge:pr-42"
    first = dep.deliver(key, merge)
    dupe = dep.deliver(key, merge)            # the duplicate delivery
    _note("duplicate result", f"key spent once: effect ran {fired['n']}x, "
          f"duplicate served from cache ({dupe == first})")
    return fired["n"] == 1 and dupe == first  # effect fired exactly once


# --- 4. The budget runs out while a release waits at the gate -------------

def budget_exhausts_at_gate() -> bool:
    app = build_team(ScriptedBrain(cost=1000))   # expensive turns
    cfg = _cfg("payday")
    treasury = Budget(allowance=1500)
    paused = app.invoke(initial_state("expensive refactor"), cfg)
    treasury.spent = app.get_state(cfg).values["spent"]
    wound_down = "__interrupt__" in paused and treasury.exhausted()

    # Wind-down banks the checkpoint and holds the approval; Monday tops up.
    treasury.allowance += 2000
    final = _resume_to_end(app, cfg, app.invoke(Command(resume=True), cfg))
    _note("budget runaway", f"wound down at the gate (spent {treasury.spent} "
          f">= 1500: {wound_down}), approval held; topped up and "
          f"shipped={final['status'] == 'shipped'}")
    return wound_down and final["status"] == "shipped"


# --- 5. A new version is deployed mid-run ---------------------------------

def deploy_mid_run() -> bool:
    saver = InMemorySaver()
    cfg = _cfg("rolling")
    app_v1 = build_team(ScriptedBrain(), checkpointer=saver)
    app_v1.invoke(initial_state("ship under a rollout"), cfg)  # parks at gate

    # The deploy: a freshly compiled graph (newer code) resumes the parked run
    # from the same journal and the same thread.
    app_v2 = build_team(ScriptedBrain(), checkpointer=saver)
    final = _resume_to_end(
        app_v2, cfg, app_v2.invoke(Command(resume=True), cfg))
    _note("deploy mid-run", f"parked run woke under a fresh graph and folded "
          f"its journal; shipped={final['status'] == 'shipped'}")
    return final["status"] == "shipped"


# --- 6. A human breaks in at 3 a.m. ---------------------------------------

def civil_interrupt() -> bool:
    app = build_team(ScriptedBrain())
    cfg = _cfg("threeam")
    # On a checkpointed runtime a human stop lands at the next turn boundary;
    # the merge gate is exactly such a boundary --- a consistent,
    # resumable cut.
    paused = app.invoke(initial_state("routine nightly change"), cfg)
    resumable = ("__interrupt__" in paused
                 and app.get_state(cfg).next == ("gate",))
    final = _resume_to_end(app, cfg, app.invoke(Command(resume=True), cfg))
    _note("3 a.m. interrupt", f"civil stop at a turn boundary "
          f"(resumable={resumable}); resumed and "
          f"shipped={final['status'] == 'shipped'}")
    return resumable and final["status"] == "shipped"


INJECTIONS = (
    crash_mid_run, test_hangs, duplicate_tool_result,
    budget_exhausts_at_gate, deploy_mid_run, civil_interrupt,
)


def run_chaos_day() -> list[bool]:
    """Run every injection; return one boring/surprising verdict apiece."""
    return [injection() for injection in INJECTIONS]


def main() -> None:
    print("chaos day: injecting the six failures from the inventory...\n")
    verdicts = run_chaos_day()
    boring = sum(verdicts)
    print(f"\nmorning log: {len(verdicts)} injections, "
          f"{boring} boring entries, "
          f"none paged a human before nine.")
    if boring != len(verdicts):
        raise SystemExit(
            "a surprise on chaos day is a defect in the machinery")


if __name__ == "__main__":
    main()
