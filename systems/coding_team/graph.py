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
from .state import NO_CAP, TeamState, initial_state

MAX_TURNS = 3

# Transient faults are worth retrying; a bug that fails identically is not.
_TESTER_RETRY = RetryPolicy(max_attempts=3, initial_interval=0.05,
                            retry_on=(TimeoutError,))


def build_team(brain: Brain, *, checkpointer: object | None = None):
    """Compile the team graph. The merge is gated by a human interrupt; drive
    it to completion with :func:`run_team`, which supplies the approval."""

    def _wound_down(state: TeamState, role: str) -> dict | None:
        # The treasury has a ceiling the nodes can see: a node that finds it
        # spent refuses to spend more --- wind-down at the node boundary,
        # not a bill discovered afterwards.
        if state["spent"] >= state.get("allowance", NO_CAP):
            return {"status": "halted-budget",
                    "findings": [f"{role}: treasury exhausted; wound down"]}
        return None

    def coder(state: TeamState) -> dict:
        if (halt := _wound_down(state, "coder")) is not None:
            return halt
        d = brain.code(state)
        return {"diff": d["diff"], "spent": d["cost"], "status": "review",
                "turn": state["turn"] + 1,
                "findings": [f"coder: {d['note']}"]}

    def reviewer(state: TeamState) -> dict:
        if (halt := _wound_down(state, "reviewer")) is not None:
            return halt
        d = brain.review(state)
        out: dict = {"verdict": d["verdict"], "spent": d["cost"],
                     "findings": [f"reviewer: {d['reason']} "
                                  f"({d['verdict']})"]}
        if d["verdict"] != "accept" and state["turn"] >= MAX_TURNS:
            out["status"] = "rejected"   # the cap is a terminal verdict,
        return out                       # not an eternal "review"

    def gate(state: TeamState) -> dict:
        # Human-in-the-loop: the run pauses here until an approval is
        # supplied. Only a literal True approves --- a truthy string
        # ("false", say) must not wave a merge through.
        approved = interrupt({"action": "merge", "diff": state["diff"]})
        ok = approved is True
        return {"approved": ok, "status": "test" if ok else "rejected"}

    def tester(state: TeamState) -> dict:
        if (halt := _wound_down(state, "tester")) is not None:
            return halt
        d = brain.test(state)
        return {"suite": d["suite"], "spent": d["cost"],
                "status": "shipped" if d["suite"] == "green" else "broken",
                "findings": [f"tester: suite {d['suite']}"]}

    def after_review(state: TeamState) -> str:
        if state["status"] == "halted-budget":
            return END
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
