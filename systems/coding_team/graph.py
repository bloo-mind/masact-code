"""The hardened coding team as a LangGraph state graph (Chapter 23).

The plain-Python version of every mechanism here lives in ``foundations/`` ---
the loop, the journal, the ACCEPT gate, the retry-and-idempotency wrapper.
This is the same machinery realised in the framework the book teaches: typed
state with reducers, a checkpointer for persistence and time-travel, a
human-in-the-loop interrupt at the merge, per-node retries, and a shared
budget. The graph is model-independent; it takes a
:class:`~systems.coding_team.brains.Brain`.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy, interrupt

from .brains import Brain
from .state import TeamState, initial_state

MAX_TURNS = 3

# Transient faults are worth retrying; a bug that fails identically is not.
_TESTER_RETRY = RetryPolicy(max_attempts=3, initial_interval=0.05,
                            retry_on=(TimeoutError,))


def build_team(brain: Brain, *, checkpointer: object | None = None):
    """Compile the team graph. The merge is gated by a human interrupt; drive
    it to completion with :func:`run_team`, which supplies the approval."""

    def coder(state: TeamState) -> dict:
        d = brain.code(state)
        return {"diff": d["diff"], "spent": d["cost"], "status": "review",
                "turn": state["turn"] + 1,
                "findings": [f"coder: {d['note']}"]}

    def reviewer(state: TeamState) -> dict:
        d = brain.review(state)
        return {"verdict": d["verdict"], "spent": d["cost"],
                "findings": [f"reviewer: {d['reason']} ({d['verdict']})"]}

    def gate(state: TeamState) -> dict:
        # Human-in-the-loop: the run pauses here until an approval
        # is supplied.
        approved = interrupt({"action": "merge", "diff": state["diff"]})
        return {"approved": bool(approved),
                "status": "test" if approved else "rejected"}

    def tester(state: TeamState) -> dict:
        d = brain.test(state)
        return {"suite": d["suite"], "spent": d["cost"],
                "status": "shipped" if d["suite"] == "green" else "broken",
                "findings": [f"tester: suite {d['suite']}"]}

    def after_review(state: TeamState) -> str:
        if state["verdict"] == "accept":
            return "gate"
        return "coder" if state["turn"] < MAX_TURNS else END

    def after_gate(state: TeamState) -> str:
        return "tester" if state["approved"] else END

    g = StateGraph(TeamState)
    g.add_node("coder", coder)
    g.add_node("reviewer", reviewer)
    g.add_node("gate", gate)
    g.add_node("tester", tester, retry_policy=_TESTER_RETRY)
    g.add_edge(START, "coder")
    g.add_edge("coder", "reviewer")
    g.add_conditional_edges("reviewer", after_review, ["gate", "coder", END])
    g.add_conditional_edges("gate", after_gate, ["tester", END])
    g.add_edge("tester", END)
    return g.compile(checkpointer=checkpointer or InMemorySaver())


def run_team(app: object, task: str, thread_id: str = "team",
             approve: bool = True) -> TeamState:
    """Drive the graph to completion, answering the human gate with
    ``approve``.

    A real deployment parks at the interrupt and resumes when a person clicks;
    here we supply the decision directly so the run is non-interactive.
    """
    from langgraph.types import Command

    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(initial_state(task), config)
    while "__interrupt__" in result:                # the merge gate paused us
        result = app.invoke(Command(resume=approve), config)
    return result
