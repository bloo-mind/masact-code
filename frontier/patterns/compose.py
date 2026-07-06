"""Composition voids warranties (Chapter 21's warning).

Each pattern's failure signature is stated for the pattern *in isolation*.
Wire two together and a new failure appears that neither has alone --- and,
worse, the composition often *launders* one pattern's failure through the
other's clean interface, so the outer level reports green while the inner rot
is real. Two specimens:

* :func:`supervisor_of_reflection` --- a placated reflection worker reports
  ``accept`` like any honest thread; the supervisor, seeing only that
  ``accept``, certifies the subtask. Placation is hidden one level up.
* :func:`router_over_pipeline` --- a single misroute at the head selects the
  wrong pipeline; every downstream stage then runs faithfully on a wrong
  premise, so the *process* is green end-to-end while solving the wrong task.
  The misroute is invisible in the journal, exactly as in isolation: only the
  output oracle (the correct specialist) reveals it.

Each returns ``(RunResult, description)``: the run whose failure the paired
instrument still identifies --- the journal for placation, the output oracle
for the misroute --- and a one-line statement of the emergent failure mode.
"""

from __future__ import annotations

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

_DIFF = "+ return xs[0] if xs else None"


def supervisor_of_reflection() -> tuple[RunResult, str]:
    """Supervisor over a reflection worker: placation laundered upward."""
    r = RunResult(task="ship the validation subtask under a supervisor",
                  output=_DIFF, status="shipped", quality=0.55, tokens=820)
    r.log(RUN_STARTED, r.task[:40])
    # The inner reflection loop placates: it accepts with objections still
    # open (open=2), the approval changing nothing that mattered.
    r.log(REVIEWED, "reject: round=1 spec=3 diff=36 open=3")
    r.log(REVIEWED, "reject: round=2 spec=1 diff=10 open=2")
    r.log(REVIEWED, "accept: round=3 spec=0 diff=1 open=2")
    # The worker reports its result to the supervisor as any honest thread.
    r.log(MESSAGE_SENT, "subtask: status=accept")
    # The supervisor, seeing only the accept, certifies the whole and ships.
    r.log(MESSAGE_SENT, "manager: subtask certified green")
    r.log(TESTED, "green")
    r.log(AGENT_FINISHED, "shipped")
    r.log(RUN_FINISHED, "shipped")
    desc = ("new failure: the supervisor certifies a subtask green on an "
            "ACCEPT that placation, not correctness, produced --- the "
            "warranty is laundered up the hierarchy where no detector looks.")
    return r, desc


def router_over_pipeline() -> tuple[RunResult, str]:
    """Router feeding a pipeline: a wrong premise, faithfully executed."""
    r = RunResult(task="fix an auth-token leak in the login handler",
                  output=_DIFF, status="shipped", quality=0.6, tokens=760)
    r.log(RUN_STARTED, r.task[:40])
    # The head misroutes: a security task sent to the coding pipeline. The
    # journal records only WHERE it went (``coding``); that this is wrong is
    # not in the trace --- it takes the external eval fact the router-over-
    # pipeline caller supplies (the correct specialist, ``security``).
    r.log(MESSAGE_SENT, "routed: specialist=coding")
    # Every pipeline stage then runs faithfully --- and green --- downstream.
    r.log(TOOL_DISPATCHED, "dispatch: step=s1 trigger=route t=1")
    r.log(TOOL_RETURNED, "return: step=s1 t=2")
    r.log(TOOL_DISPATCHED, "dispatch: step=s2 trigger=route t=3")
    r.log(TOOL_RETURNED, "return: step=s2 t=4")
    r.log(REVIEWED, "accept: round=1 spec=3 diff=15 open=0")
    r.log(TESTED, "green")
    r.log(AGENT_FINISHED, "shipped")
    r.log(RUN_FINISHED, "shipped")
    desc = ("new failure: one misroute at the head becomes a wrong PROCESS "
            "--- every downstream stage executes flawlessly on the wrong "
            "premise, so the pipeline is green end-to-end yet solves the "
            "wrong problem, and no stage can detect it locally.")
    return r, desc
