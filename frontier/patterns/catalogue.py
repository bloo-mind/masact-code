"""The pattern catalogue and its failure signatures (Chapter 21).

The chapter's claim is that architecture is a *catalogue choice*: nine
patterns in three families, plus three anti-patterns that look like patterns
but earn nothing. Each entry records not only what the shape *keeps* --- the
property it buys --- but the way it *fails*, because the book's discipline is
to pick a pattern by the failure you can afford, not the picture on the box.

Three scripted topology runners (:func:`supervisor_run`, :func:`peer_run`,
:func:`debate_run`) let the pattern-swap of Chapter 21 be scored on the rig's
four columns: the same task routed through three shapes, measured once.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..rig import (
    AGENT_FINISHED,
    MESSAGE_SENT,
    REVIEWED,
    RUN_FINISHED,
    RUN_STARTED,
    TESTED,
    TOOL_DISPATCHED,
    TOOL_RETURNED,
    RunResult,
)


class Family(Enum):
    """The three families a pattern belongs to --- plus the anti-patterns,
    which mimic a family without buying its property."""

    DELEGATION = "delegation"
    PROCESS = "process"
    COLLECTIVE = "collective"
    ANTIPATTERN = "anti-pattern"


@dataclass(frozen=True)
class Pattern:
    """One catalogue entry: what the shape is, what it keeps, how it fails."""

    name: str
    family: Family
    shape: str               # the topology in a phrase
    keeps: str               # the property the shape buys
    failure_signature: str   # the way it fails (usually legible in the
    #                          journal --- the router's misroute is the one
    #                          that is not: only the output reveals it)


# --- The nine patterns, three families -----------------------------------

CATALOGUE: list[Pattern] = [
    # Delegation: one agent decides who does the work.
    Pattern(
        "router", Family.DELEGATION,
        "a dispatcher forwards each request to one specialist",
        "cheap fan-out; the right expert on the right request",
        "misroute: a perfectly healthy run of the wrong kind --- routed to "
        "the wrong specialist, yet clean and all-green. INVISIBLE in the "
        "journal (nothing in the trace is anomalous); only the OUTPUT, "
        "judged against the specialist the task required, reveals it"),
    Pattern(
        "supervisor", Family.DELEGATION,
        "a manager decomposes the task and assigns the parts",
        "a single point of planning and integration",
        "confident decomposition of the wrong shape: the parts are "
        "executed faithfully but do not reassemble into the task"),
    Pattern(
        "hand-off", Family.DELEGATION,
        "control passes agent to agent, one holder at a time",
        "clear ownership; no two agents act at once",
        "baton-drop: the handed-off context is lost or truncated at "
        "the seam, so the receiver resumes on a thinner state"),
    Pattern(
        "hierarchical team", Family.DELEGATION,
        "managers of managers; work flows down, results up",
        "depth: a big task fits under one root",
        "whisper game: leaf facts and the root's integration claim "
        "diverge, the gap widening with each level of relay"),
    # Process: the pipeline of steps is the architecture.
    Pattern(
        "planner-executor", Family.PROCESS,
        "a planner fixes a plan; an executor runs its steps",
        "a legible plan you can audit before acting",
        "stale plan: a tool result falsifies a step, yet the executor "
        "keeps dispatching on schedule --- a contradiction with a "
        "timestamp"),
    Pattern(
        "reflection loop", Family.PROCESS,
        "a worker drafts; a critic reviews; repeat to a cap",
        "self-correction without a second model",
        "placation (critique decays to politeness as diffs vanish) or "
        "a polish loop (the cap strikes, diffs refuse to shrink)"),
    # Collective: many peers, no single decider.
    Pattern(
        "debate", Family.COLLECTIVE,
        "agents argue opposing positions to a judged verdict",
        "adversarial scrutiny; errors get challenged",
        "chorus: positions collapse after round one and later rounds "
        "add no argument --- agreement faster than scrutiny"),
    Pattern(
        "blackboard", Family.COLLECTIVE,
        "agents read and write a shared, versioned workspace",
        "loose coupling; contributions accrete on one surface",
        "stampede (a burst of near-simultaneous dispatches off one "
        "posting) or a stale read (an artefact built on an "
        "out-of-date version)"),
    Pattern(
        "peer network", Family.COLLECTIVE,
        "equals message equals with no central authority",
        "no bottleneck; resilience to any one agent",
        "incoherence: without a decider, local edits cascade into a "
        "globally inconsistent result no peer can see whole"),
    # --- The three anti-patterns: shape without the property ------------
    Pattern(
        "group chat", Family.ANTIPATTERN,
        "every agent on one channel, all speaking",
        "nothing durable --- it mimics collaboration",
        "no closure: everyone talks, no one decides; tokens burn "
        "while the task never reaches a verdict"),
    Pattern(
        "everything-agent", Family.ANTIPATTERN,
        "one agent holding every tool and every role",
        "nothing --- it mimics a team inside one context",
        "context collapse: no separation of concerns, so the single "
        "context thrashes and no role is done well"),
    Pattern(
        "gratuitous agent", Family.ANTIPATTERN,
        "a multi-agent shape where one agent would do",
        "nothing --- it mimics scale",
        "coordination tax for no parallel work: the wiring costs "
        "latency and tokens the task never needed"),
]


# --- Three scripted topology runners for the pattern-swap ----------------
#
# Deterministic, model-free stand-ins so the swap can be *scored* on the four
# columns. Each produces a healthy journal in its own shape; none raises a
# failure signature (the injections module does the breaking).

def _finish(r: RunResult, status: str = "shipped") -> RunResult:
    r.log(AGENT_FINISHED, status)
    r.log(RUN_FINISHED, status)
    return r


def supervisor_run(task: str) -> RunResult:
    """Delegation: a manager decomposes, workers execute, one review."""
    r = RunResult(task=task, output="+ return xs[0] if xs else None",
                  status="shipped", quality=0.9, tokens=620)
    r.log(RUN_STARTED, task[:40])
    r.log(MESSAGE_SENT, "manager: decompose into 3 parts")
    r.log(TOOL_DISPATCHED, "dispatch: step=s1 trigger=plan t=1")
    r.log(TOOL_RETURNED, "return: step=s1 t=2")
    r.log(TOOL_DISPATCHED, "dispatch: step=s2 trigger=plan t=3")
    r.log(TOOL_RETURNED, "return: step=s2 t=4")
    r.log(REVIEWED, "accept: round=1 spec=3 diff=18")
    r.log(TESTED, "green")
    return _finish(r)


def peer_run(task: str) -> RunResult:
    """Collective: equals message equals; more chatter, looser control."""
    r = RunResult(task=task, output="+ return xs[0] if xs else None",
                  status="shipped", quality=0.74, tokens=940)
    r.log(RUN_STARTED, task[:40])
    r.log(MESSAGE_SENT, "peer: a proposes edit")
    r.log(MESSAGE_SENT, "peer: b amends")
    r.log(MESSAGE_SENT, "peer: c reconciles")
    r.log(TOOL_DISPATCHED, "dispatch: step=e1 trigger=a t=1")
    r.log(TOOL_RETURNED, "return: step=e1 t=2")
    r.log(TESTED, "green")
    return _finish(r)


def debate_run(task: str) -> RunResult:
    """Collective: two positions argued to a judged verdict (healthy)."""
    r = RunResult(task=task, output="+ return xs[0] if xs else None",
                  status="shipped", quality=0.86, tokens=1240)
    r.log(RUN_STARTED, task[:40])
    r.log(MESSAGE_SENT, "debate: round=1 stances=2 newargs=2")
    r.log(MESSAGE_SENT, "debate: round=2 stances=2 newargs=1")
    r.log(MESSAGE_SENT, "judge: verdict for position a")
    r.log(TESTED, "green")
    return _finish(r)
