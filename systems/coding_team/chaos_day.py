"""Chaos day (Chapter 23, the finale of the assembled system).

Inject the six failures from the chapter's inventory --- a crash, a hang, a
duplicate, a runaway bill, a deploy, and a human breaking in --- against the
one assembled team, and confirm that each is *boring*: six injections, six
one-line entries in the morning log, none of them requiring a human before
nine. A surprise here would be a defect in the machinery, so the script
doubles as an executable assertion that the dependability mechanisms hold.

Honesty about scope, before anything runs. What each scene *exercises* is
real --- checkpoint resume after a mid-node death, a retry policy driven to
exhaustion and the task shelved, an idempotency key spending exactly once,
the graph refusing to spend past its allowance, a recompiled graph adopting
a parked thread, an interrupt landing at a consistent boundary. What frames
each scene is simulated: the "process" that dies is this process (a fresh
graph instance stands in for the restart, and ``InMemorySaver`` for the
durable store), the "hang" is the timeout wrapper's verdict delivered
instantly, the dead-letter queue is a list in the driver, and the "deploy"
recompiles identical code. The chapter's exercises graduate each stand-in
to the real thing; this script certifies the mechanisms, not the ops.

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
    saver = InMemorySaver()    # stands in for the durable, off-process store
    brain = _CrashOnce()
    cfg = _cfg("nightly")
    app = build_team(brain, checkpointer=saver)
    try:
        app.invoke(initial_state("harden the parser"), cfg)
    except RuntimeError:
        pass                                  # the "process" died mid-review

    # A fresh graph instance --- standing in for the restarted process ---
    # reads the same checkpoint and carries on from the cut.
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
    # The tester "hangs": the scripted brain raises TimeoutError at once,
    # standing in for a real timeout wrapper's verdict after its deadline.
    # What is under test is what happens next --- the node's RetryPolicy
    # backs off, exhausts, and the driver shelves the task (a list standing
    # in for the dead-letter queue) with its trace, rather than retrying it
    # into the ground.
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
    # The graph itself enforces the allowance: coder (1000) plus reviewer
    # (500) drain the 1500-token treasury exactly as the run parks at the
    # merge gate, and when the approved run reaches the tester, the node
    # refuses to spend and winds the run down --- the mechanism, not an
    # accountant arriving after the bill.
    app = build_team(ScriptedBrain(cost=1000))   # expensive turns
    cfg = _cfg("payday")
    paused = app.invoke(
        initial_state("expensive refactor", allowance=1500), cfg)
    halted = _resume_to_end(app, cfg, paused)    # approve; tester refuses
    spent = halted["spent"]
    wound_down = (halted["status"] == "halted-budget"
                  and spent <= 1500 and "__interrupt__" in paused)

    # Monday tops the treasury up at the gate's checkpoint --- time-travel,
    # the Chapter 23 mechanism --- and the resumed run ships.
    app.update_state(cfg, {"allowance": 3500}, as_node="gate")
    final = _resume_to_end(app, cfg, app.invoke(None, cfg))
    _note("budget runaway",
          f"graph wound itself down (spent {spent} of 1500, "
          f"status halted-budget: {wound_down}); topped up and "
          f"shipped={final['status'] == 'shipped'}")
    return wound_down and final["status"] == "shipped"


# --- 5. A new version is deployed mid-run ---------------------------------

def deploy_mid_run() -> bool:
    saver = InMemorySaver()
    cfg = _cfg("rolling")
    app_v1 = build_team(ScriptedBrain(), checkpointer=saver)
    app_v1.invoke(initial_state("ship under a rollout"), cfg)  # parks at gate

    # The "deploy": a freshly compiled graph resumes the parked run from the
    # same store and thread. (The recompiled code is identical here --- what
    # is exercised is graph-adopts-parked-thread, not a schema migration,
    # which needs the reducer discipline the chapter describes.)
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
    # the merge gate is exactly such a boundary --- a consistent, resumable
    # cut. (In this small graph the gate is the only planned boundary, so
    # the "3 a.m. break-in" and the ordinary approval park coincide; the
    # property certified is that the cut is consistent and resumable.)
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
