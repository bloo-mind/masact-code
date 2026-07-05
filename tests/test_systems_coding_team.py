"""Hermetic tests for the Chapter 23 LangGraph team.

Everything here runs on a ScriptedBrain --- no model, no key, no network ---
so what is under test is the framework machinery: reducers, checkpointing, the
human-gate interrupt, budget accumulation, retries, and time-travel.
"""

import pytest

pytest.importorskip("langgraph")

from langgraph.checkpoint.memory import InMemorySaver  # noqa: E402
from langgraph.types import Command  # noqa: E402

from systems.coding_team import (  # noqa: E402
    ScriptedBrain, build_team, initial_state, run_team,
)


def _cfg(tid="t"):
    return {"configurable": {"thread_id": tid}}


def test_team_ships_and_reducers_accumulate():
    app = build_team(ScriptedBrain())
    final = run_team(app, "fix the parser", thread_id="ship")
    assert final["status"] == "shipped"
    assert final["suite"] == "green"
    # findings accumulate from three nodes via the Annotated reducer
    assert len(final["findings"]) == 3
    assert final["findings"][0].startswith("coder:")
    # the budget summed the three debits (120 + 60 + 40)
    assert final["spent"] == 220


def test_human_gate_interrupts_then_resumes():
    app = build_team(ScriptedBrain())
    cfg = _cfg("gate")
    paused = app.invoke(initial_state("fix it"), cfg)
    # the run parked at the merge gate, before the tester ran
    assert "__interrupt__" in paused
    assert app.get_state(cfg).values["status"] == "review" or \
        app.get_state(cfg).next == ("gate",)
    # a human approves; the run resumes to shipped
    resumed = app.invoke(Command(resume=True), cfg)
    assert resumed["status"] == "shipped"


def test_human_gate_rejection_blocks_the_merge():
    app = build_team(ScriptedBrain())
    final = run_team(app, "risky change", thread_id="no", approve=False)
    assert final["status"] == "rejected"
    assert final["suite"] == ""            # the tester never ran


def test_reviewer_rejection_loops_then_gives_up():
    app = build_team(ScriptedBrain(verdict="reject"))
    final = run_team(app, "never good enough", thread_id="loop")
    # the coder retried up to the turn cap, then the run ended un-merged
    assert final["turn"] == 3
    assert final["verdict"] == "reject"
    assert final["approved"] is False
    assert len(final["findings"]) == 6     # coder + reviewer, three rounds


def test_tester_retry_survives_a_transient_fault():
    # the tester raises TimeoutError once; the node's RetryPolicy recovers
    app = build_team(ScriptedBrain(test_faults=1))
    final = run_team(app, "flaky suite", thread_id="retry")
    assert final["status"] == "shipped"


def test_checkpointer_enables_time_travel():
    saver = InMemorySaver()
    app = build_team(ScriptedBrain(), checkpointer=saver)
    cfg = _cfg("tt")
    run_team(app, "fix it", thread_id="tt")
    history = list(app.get_state_history(cfg))   # newest first
    assert len(history) >= 4                # a checkpoint per superstep
    # the latest checkpoint is shipped; a start checkpoint sits in the past
    assert history[0].values["status"] == "shipped"
    assert any(h.values.get("status") == "start" for h in history)


def test_state_is_recomputed_from_the_checkpoint_not_shared():
    # two threads on one app do not bleed into each other
    app = build_team(ScriptedBrain())
    a = run_team(app, "task A", thread_id="A")
    b = run_team(app, "task B", thread_id="B")
    assert a["task"] == "task A" and b["task"] == "task B"
    assert a["spent"] == b["spent"] == 220
