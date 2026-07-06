"""Break each pattern its own way, so the paired detector fires (Ch 21).

Each ``*_run`` builds a :class:`~frontier.rig.RunResult` whose journal carries
one failure signature and nothing on its face to betray it: the diff is
plausible, the finish is green, ``r.failures`` is empty --- the failure lives
in the *shape* of the journal, which the matching detector reads. Every broken
run is paired with a structurally faithful ``healthy_*`` run on which the same
detector returns ``False`` (no false positive from mere structure).

All builders are deterministic and model-free; the journal format is the one
documented in :mod:`frontier.patterns.signatures`.
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


def _new(task: str, quality: float = 0.9, tokens: int = 300) -> RunResult:
    r = RunResult(task=task, output=_DIFF, status="shipped",
                  quality=quality, tokens=tokens)
    r.log(RUN_STARTED, task[:40])
    return r


def _green_finish(r: RunResult) -> RunResult:
    r.log(AGENT_FINISHED, "shipped")
    r.log(RUN_FINISHED, "shipped")
    return r


# --- Router: misroute ----------------------------------------------------

CORRECT_SPECIALIST = "security"


def misrouted_run() -> RunResult:
    """A security task routed to the coding specialist --- all green, wrong
    expert. The journal records only *where* it was routed (``coding``); that
    this was wrong is not in the trace at all. The verdict needs an external
    eval fact, :data:`CORRECT_SPECIALIST`, which the journal never carries ---
    the clean run is the trap. See :func:`~frontier.patterns.signatures`."""
    r = _new("fix an auth-token leak in the login handler")
    r.log(MESSAGE_SENT, "routed: specialist=coding")
    r.log(TOOL_DISPATCHED, "dispatch: step=s1 trigger=route t=1")
    r.log(TOOL_RETURNED, "return: step=s1 t=2")
    r.log(REVIEWED, "accept: round=1 spec=3 diff=14 open=0")
    r.log(TESTED, "green")
    return _green_finish(r)


def healthy_routed_run() -> RunResult:
    """The same shape, routed correctly (to :data:`CORRECT_SPECIALIST`):
    judged against that eval fact the detector must stay silent. Note the
    journal is otherwise identical to :func:`misrouted_run` --- the only
    difference is the specialist token, and only the external fact can say
    which of the two is the mistake."""
    r = _new("fix an auth-token leak in the login handler")
    r.log(MESSAGE_SENT, f"routed: specialist={CORRECT_SPECIALIST}")
    r.log(TOOL_DISPATCHED, "dispatch: step=s1 trigger=route t=1")
    r.log(TOOL_RETURNED, "return: step=s1 t=2")
    r.log(REVIEWED, "accept: round=1 spec=3 diff=14 open=0")
    r.log(TESTED, "green")
    return _green_finish(r)


# --- Planner-executor: stale plan ----------------------------------------

def stale_plan_run() -> RunResult:
    """A tool result falsifies step s2, yet s2 and s3 dispatch on schedule ---
    a contradiction with a timestamp."""
    r = _new("migrate the config loader to the new schema")
    r.log(MESSAGE_SENT, "plan: steps=s1,s2,s3")
    r.log(TOOL_DISPATCHED, "dispatch: step=s1 trigger=plan t=1")
    r.log(TOOL_RETURNED, "return: step=s1 t=2")
    r.log(TOOL_RETURNED, "return: falsifies=s2 t=3")   # s2's premise is gone
    r.log(TOOL_DISPATCHED, "dispatch: step=s2 trigger=plan t=4")
    r.log(TOOL_DISPATCHED, "dispatch: step=s3 trigger=plan t=5")
    r.log(TESTED, "green")
    return _green_finish(r)


def healthy_plan_run() -> RunResult:
    """Same falsification, but the planner replans before dispatching on."""
    r = _new("migrate the config loader to the new schema")
    r.log(MESSAGE_SENT, "plan: steps=s1,s2,s3")
    r.log(TOOL_DISPATCHED, "dispatch: step=s1 trigger=plan t=1")
    r.log(TOOL_RETURNED, "return: step=s1 t=2")
    r.log(TOOL_RETURNED, "return: falsifies=s2 t=3")
    r.log(MESSAGE_SENT, "replan: drop s2, re-derive s3")
    r.log(TOOL_DISPATCHED, "dispatch: step=s3 trigger=plan t=5")
    r.log(TESTED, "green")
    return _green_finish(r)


# --- Reflection loop: placation ------------------------------------------

def placated_run() -> RunResult:
    """Three review rounds that end in placation: three objections are raised
    and the diff shrinks toward empty (40 -> 12 -> 1), but two objections are
    never answered --- the critic accepts with ``open=2`` still standing. The
    approval changed nothing that mattered. The tell is the open count at
    ``accept``, not the shrinking diff (a healthy review shrinks too)."""
    r = _new("tighten input validation on the upload endpoint")
    r.log(REVIEWED, "reject: round=1 spec=3 diff=40 open=3")
    r.log(REVIEWED, "reject: round=2 spec=1 diff=12 open=2")
    r.log(REVIEWED, "accept: round=3 spec=0 diff=1 open=2")
    r.log(TESTED, "green")
    return _green_finish(r)


def healthy_review_run() -> RunResult:
    """A real correction that converges: the diff shrinks (40 -> 28) exactly
    as in a placation, but every objection is *resolved* --- the critic
    accepts with ``open=0``. Structurally near-identical to
    :func:`placated_run`; only the open count separates honest convergence
    from acceptance by politeness. Neither placation nor a polish loop."""
    r = _new("tighten input validation on the upload endpoint")
    r.log(REVIEWED, "reject: round=1 spec=3 diff=40 open=2")
    r.log(REVIEWED, "accept: round=2 spec=3 diff=28 open=0")
    r.log(TESTED, "green")
    return _green_finish(r)


# --- Reflection loop: polish loop ----------------------------------------

def polish_loop_run() -> RunResult:
    """The round cap is struck; the diffs will not shrink and cycle
    (30, 25, 30, 25): revision without convergence."""
    r = _new("restyle the report module to the house guide",
             quality=0.5, tokens=900)
    r.log(REVIEWED, "reject: round=1 spec=2 diff=30")
    r.log(REVIEWED, "reject: round=2 spec=2 diff=25")
    r.log(REVIEWED, "reject: round=3 spec=2 diff=30")
    r.log(REVIEWED, "reject: round=4 spec=2 diff=25")
    r.log(MESSAGE_SENT, "round-cap: hit=4")
    r.log(TESTED, "red")
    r.status = "rejected"
    r.log(AGENT_FINISHED, "rejected")
    r.log(RUN_FINISHED, "rejected")
    return r


def healthy_capped_convergence_run() -> RunResult:
    """The round cap is struck, but the diffs shrank in earnest (40, 24, 12,
    6): the loop converged and merely ran out of rounds. A polish loop must
    NOT be read here --- hitting the cap is not the failure; refusing to
    shrink is."""
    r = _new("restyle the report module to the house guide",
             quality=0.7, tokens=760)
    r.log(REVIEWED, "reject: round=1 spec=2 diff=40 open=2")
    r.log(REVIEWED, "reject: round=2 spec=2 diff=24 open=1")
    r.log(REVIEWED, "reject: round=3 spec=2 diff=12 open=1")
    r.log(REVIEWED, "reject: round=4 spec=2 diff=6 open=1")
    r.log(MESSAGE_SENT, "round-cap: hit=4")
    r.log(TESTED, "red")
    r.status = "rejected"
    r.log(AGENT_FINISHED, "rejected")
    r.log(RUN_FINISHED, "rejected")
    return r


# --- Debate: chorus ------------------------------------------------------

def chorus_run() -> RunResult:
    """Two stances in round one; from round two the stances collapse to one
    and no new argument appears --- agreement faster than scrutiny."""
    r = _new("decide the retry policy for the queue consumer")
    r.log(MESSAGE_SENT, "debate: round=1 stances=2 newargs=2")
    r.log(MESSAGE_SENT, "debate: round=2 stances=1 newargs=0")
    r.log(MESSAGE_SENT, "debate: round=3 stances=1 newargs=0")
    r.log(MESSAGE_SENT, "judge: verdict for position a")
    r.log(TESTED, "green")
    return _green_finish(r)


def healthy_debate_run() -> RunResult:
    """Stances stay divided and new arguments keep arriving: real debate."""
    r = _new("decide the retry policy for the queue consumer")
    r.log(MESSAGE_SENT, "debate: round=1 stances=2 newargs=2")
    r.log(MESSAGE_SENT, "debate: round=2 stances=2 newargs=1")
    r.log(MESSAGE_SENT, "judge: verdict for position b")
    r.log(TESTED, "green")
    return _green_finish(r)


# --- Hierarchical team: whisper divergence -------------------------------

def whisper_run() -> RunResult:
    """The leaf measured 42; each relay up drifts further (48, 55, 63) so the
    root integrates a claim the gap widens toward."""
    r = _new("summarise the load-test numbers up the tree")
    r.log(TOOL_RETURNED, "leaf: depth=3 value=42")
    r.log(MESSAGE_SENT, "relay: depth=2 value=48")
    r.log(MESSAGE_SENT, "relay: depth=1 value=55")
    r.log(MESSAGE_SENT, "relay: depth=0 value=63")
    r.log(TESTED, "green")
    return _green_finish(r)


def healthy_whisper_run() -> RunResult:
    """Each relay preserves the leaf value exactly: no divergence."""
    r = _new("summarise the load-test numbers up the tree")
    r.log(TOOL_RETURNED, "leaf: depth=3 value=42")
    r.log(MESSAGE_SENT, "relay: depth=2 value=42")
    r.log(MESSAGE_SENT, "relay: depth=1 value=42")
    r.log(MESSAGE_SENT, "relay: depth=0 value=42")
    r.log(TESTED, "green")
    return _green_finish(r)


def healthy_whisper_rounding_run() -> RunResult:
    """Faithful summarisation with benign rounding drift: the leaf is 42 and
    the root relays 43 --- a one-unit gap within tolerance. The direction
    matches a whisper game (the gap technically widens by a hair), but the
    magnitude does not clear the tolerance, so the detector must stay silent:
    rounding is not the whisper game."""
    r = _new("summarise the load-test numbers up the tree")
    r.log(TOOL_RETURNED, "leaf: depth=3 value=42")
    r.log(MESSAGE_SENT, "relay: depth=2 value=42")
    r.log(MESSAGE_SENT, "relay: depth=1 value=42")
    r.log(MESSAGE_SENT, "relay: depth=0 value=43")
    r.log(TESTED, "green")
    return _green_finish(r)


# --- Blackboard: stampede ------------------------------------------------

def stampede_run() -> RunResult:
    """One posting wakes four agents at once and they all pile onto the SAME
    board region (``index``): a burst of near-simultaneous same-trigger
    dispatches doing interchangeable work, so the team rebuilds one index four
    times over. Duplication, not breadth, is the failure."""
    r = _new("rebuild the index after the schema posting", tokens=1100)
    r.log(TOOL_RETURNED, "post: key=schema ver=2 t=7")
    r.log(TOOL_DISPATCHED, "dispatch: step=w1 trigger=e7 region=index t=7")
    r.log(TOOL_DISPATCHED, "dispatch: step=w2 trigger=e7 region=index t=7")
    r.log(TOOL_DISPATCHED, "dispatch: step=w3 trigger=e7 region=index t=7")
    r.log(TOOL_DISPATCHED, "dispatch: step=w4 trigger=e7 region=index t=7")
    r.log(TESTED, "green")
    return _green_finish(r)


def healthy_fanout_run() -> RunResult:
    """Healthy parallelism, not a stampede: one posting fans four workers out
    off the SAME trigger ``e7``, but each takes a DISTINCT board region ---
    breadth, not duplicated work. The detector must stay silent even though
    the burst and the trigger match the stampede exactly; only the work
    targets differ."""
    r = _new("rebuild the derived views after the schema posting", tokens=980)
    r.log(TOOL_RETURNED, "post: key=schema ver=2 t=7")
    r.log(TOOL_DISPATCHED, "dispatch: step=w1 trigger=e7 region=index t=7")
    r.log(TOOL_DISPATCHED, "dispatch: step=w2 trigger=e7 region=cache t=7")
    r.log(TOOL_DISPATCHED, "dispatch: step=w3 trigger=e7 region=search t=7")
    r.log(TOOL_DISPATCHED, "dispatch: step=w4 trigger=e7 region=docs t=7")
    r.log(TESTED, "green")
    return _green_finish(r)


def healthy_dispatch_run() -> RunResult:
    """Dispatches spread across distinct triggers: no burst at all."""
    r = _new("rebuild the index after the schema posting")
    r.log(TOOL_RETURNED, "post: key=schema ver=2 t=7")
    r.log(TOOL_DISPATCHED, "dispatch: step=w1 trigger=e7 region=index t=7")
    r.log(TOOL_RETURNED, "return: step=w1 t=8")
    r.log(TOOL_DISPATCHED, "dispatch: step=w2 trigger=e8 region=index t=9")
    r.log(TESTED, "green")
    return _green_finish(r)


# --- Blackboard: stale read ----------------------------------------------

def stale_read_run() -> RunResult:
    """The artefact reads schema ver=1 though ver=2 was posted earlier at
    t=3, well before the read at t=5."""
    r = _new("generate the client from the posted schema")
    r.log(TOOL_RETURNED, "post: key=schema ver=1 t=1")
    r.log(TOOL_RETURNED, "post: key=schema ver=2 t=3")
    r.log(MESSAGE_SENT, "read: key=schema ver=1 t=5")
    r.log(TESTED, "green")
    return _green_finish(r)


def healthy_read_run() -> RunResult:
    """The read takes the newest posted version: no staleness."""
    r = _new("generate the client from the posted schema")
    r.log(TOOL_RETURNED, "post: key=schema ver=1 t=1")
    r.log(TOOL_RETURNED, "post: key=schema ver=2 t=3")
    r.log(MESSAGE_SENT, "read: key=schema ver=2 t=5")
    r.log(TESTED, "green")
    return _green_finish(r)


def clean_run() -> RunResult:
    """A bare healthy run --- no signature-bearing entries at all. No detector
    should fire on it (the strong no-false-positive baseline)."""
    r = _new("add a null guard to the parser")
    r.log(REVIEWED, "accept: round=1 spec=3 diff=16")
    r.log(TESTED, "green")
    return _green_finish(r)
