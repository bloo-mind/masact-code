"""Chapter 19's framework scorecard: one job, several framework positions.

The lab builds the running team's bounded coding job in several framework
positions and scores four columns --- tokens, latency, lines of code, and
the column that repays the exercise, failure behaviour. Tokens and latency
spread modestly (the model is held fixed underneath); lines of code spread
dramatically and *mislead* --- the declaration wins it, and the victory
measures the decisions you did not get to make. Failure behaviour is the
real separator: inject a tool error mid-turn, a model timeout, and a
malformed response, and record what each candidate actually does.

Dated (2026): the lines-of-code counts and the fault dispositions are
illustrative snapshots. The durable content is the *method* --- four
columns and a failure census --- not the particular cells.
"""

from __future__ import annotations

from enum import Enum

from ..rig import (
    MESSAGE_SENT, REVIEWED, TOOL_DISPATCHED, TOOL_RETURNED, RunResult,
    Runner, four_columns,
)

# --- Column three: lines of code to build the team each way ---------------

# Dated (2026): approximate lines to stand the team up in each position.
# The point is the SPREAD, not the cells --- the cheapest declaration hides
# the most defaulted-away decisions, which the failure column then bills.
LOC: dict[str, int] = {
    "crewai": 12,            # a declarative crew: role, goal, task declared
    "plain": 15,             # one agent, one pass (frontier.plain_runner)
    "claude_agent_sdk": 30,  # a vendor agent SDK adapter
    "langgraph": 90,         # the Chapter 23 graph (systems/coding_team)
}


def scorecard(runners: dict[str, Runner], task: str,
              repeats: int = 1) -> dict[str, dict[str, float]]:
    """Run each runner on ``task`` and report the four columns plus LoC.

    Tokens, latency, quality and the failure count come from the shared rig
    (:func:`four_columns`); lines of code is the dated fifth cell that the
    book warns reads backwards.
    """
    board: dict[str, dict[str, float]] = {}
    for name, runner in runners.items():
        runs = [_guarded(runner, task) for _ in range(max(1, repeats))]
        cols = four_columns(runs)
        cols["loc"] = float(LOC.get(name, 0))
        board[name] = cols
    return board


def _guarded(runner: Runner, task: str) -> RunResult:
    """Run a runner and survive its crash. A framework that dies on a task is
    not an exception to swallow --- it is a failure-behaviour data point,
    recorded as a crashed run rather than sinking the whole comparison."""
    try:
        return runner(task)
    except Exception as exc:              # noqa: BLE001 -- a crash IS data
        crashed = RunResult(task=task, status="crashed", quality=0.0)
        crashed.failures.append(f"crashed: {type(exc).__name__}")
        return crashed


# --- Column four: failure behaviour, the real separator -------------------

Fault = Enum("Fault", "TOOL_ERROR TIMEOUT MALFORMED")

# The fault-handling POLICY a runner declares --- its dated disposition. For
# each fault it either SURFACEs the fault, RETRYs it out of sight, or
# SWALLOWs it whole. This is an INPUT the runner carries; :func:`inject`
# enacts it and :func:`classify_response` then reads a verdict back off the
# OBSERVED run --- so the two are never a closed round-trip through a table.
SURFACE = "surface"
RETRY = "retry"
SWALLOW = "swallow"

# The three verdicts classify_response RECOVERS from a faulted run --- best
# to worst. Deliberately distinct strings from the policy actions above: the
# verdict is inspected off the result, never copied from the policy.
SURFACED = "surfaced_cleanly"
RETRIED = "retried_silently"
SWALLOWED = "swallowed"

# Dated (2026): an ASSUMED fault-handling policy for each named framework
# position, consulted ONLY when a runner carries no explicit policy of its
# own --- the ``--live`` CLI positions, whose true disposition we cannot
# observe hermetically. The honest split: the mechanism (inject then
# classify off the observed run) is measured; these particular cells are an
# assumption about how each real framework behaves. A position absent here,
# and any fault a policy omits, is assumed to surface honestly.
DISPOSITIONS: dict[str, dict[Fault, str]] = {
    "plain": {
        Fault.TOOL_ERROR: SWALLOW,
        Fault.TIMEOUT: SURFACE,
        Fault.MALFORMED: SWALLOW,
    },
    "langgraph": {
        Fault.TOOL_ERROR: SURFACE,
        Fault.TIMEOUT: RETRY,
        Fault.MALFORMED: SURFACE,
    },
    "claude_agent_sdk": {
        Fault.TOOL_ERROR: RETRY,
        Fault.TIMEOUT: RETRY,
        Fault.MALFORMED: SURFACE,
    },
    "crewai": {              # high abstraction tends to paper over faults
        Fault.TOOL_ERROR: RETRY,
        Fault.TIMEOUT: RETRY,
        Fault.MALFORMED: SWALLOW,
    },
}

# A runner that declares no action for a fault is assumed to surface it.
_DEFAULT_ACTION = SURFACE

# The suffix a surfaced fault leaves on ``failures`` --- read, not matched
# against any per-framework table, by classify_response.
_SURFACED_SUFFIX = ":surfaced"


def _fault_tag(fault: Fault) -> str:
    return f"fault:{fault.name.lower()}"


def attach_policy(runner: Runner, policy: dict[Fault, str]) -> Runner:
    """Attach an explicit, dated fault-handling policy to ``runner`` so
    :func:`inject` can enact it. Returns the same runner, for chaining.

    The policy is set INDEPENDENTLY of any framework name: it is the ground
    truth a faulted run must then be observed to obey.
    """
    runner.fault_policy = dict(policy)   # type: ignore[attr-defined]
    return runner


def _action_for(runner: Runner, fault: Fault) -> str:
    """The action ``runner``'s policy declares for ``fault`` (defaulting to
    :data:`SURFACE` when the runner declares none)."""
    policy = getattr(runner, "fault_policy", None) or {}
    return policy.get(fault, _DEFAULT_ACTION)


def inject(runner: Runner, fault: Fault) -> Runner:
    """Wrap ``runner`` so ``fault`` actually fires mid-run, then let the
    runner's own policy shape the OBSERVABLE outcome.

    * *surface* --- a timeout raises :class:`TimeoutError`; any other fault
      sets ``status='failed'``, empties the output, and tags ``failures``.
    * *retry* --- the fault fires and is recovered out of sight: a scar in
      the journal (dispatch / error / retry / ok) over otherwise clean,
      shipped columns.
    * *swallow* --- the fault fires and vanishes: ``status='shipped'`` over a
      silently-wrong output, with no journal trace of the fault at all.
    """
    action = _action_for(runner, fault)
    fault_tag = _fault_tag(fault)

    def run(task: str) -> RunResult:
        r = runner(task)
        if action == SURFACE:
            if fault is Fault.TIMEOUT:
                raise TimeoutError(fault_tag)
            r.status = "failed"
            r.output = ""
            r.failures.append(f"{fault.name.lower()}{_SURFACED_SUFFIX}")
            r.log(REVIEWED, f"reject: {fault_tag}")
        elif action == RETRY:
            # The fault fired and was recovered before it reached a column:
            # the journal remembers, the four columns do not.
            r.status = "shipped"
            r.log(TOOL_DISPATCHED, fault_tag)
            r.log(TOOL_RETURNED, f"error: {fault_tag}")
            r.log(TOOL_DISPATCHED, f"retry: {fault_tag}")
            r.log(TOOL_RETURNED, "ok")
            r.log(MESSAGE_SENT, f"retry: recovered from {fault_tag}")
        else:                             # SWALLOW
            # The fault fired and left no trace: the columns look spotless
            # over an output the fault has silently corrupted.
            r.status = "shipped"
            r.output = "+ return xs[0]        # (fault swallowed; wrong)"
        return r

    return run


def classify_response(result_or_exc: RunResult | BaseException,
                      fault: Fault) -> str:
    """Recover the failure-behaviour verdict by INSPECTING a faulted run (or
    the exception it raised). Consults no name -> verdict table.

    A raised fault, a failed status, or a ``:surfaced`` tag reads as a clean
    surface; a retry scar in the journal over shipped columns reads as a
    silent retry; a shipped run with no trace at all reads as the fault
    swallowed whole. ``fault`` names the fault the census injected.
    """
    del fault                            # verdict is read off the run alone
    if isinstance(result_or_exc, BaseException):
        return SURFACED
    r = result_or_exc
    surfaced = any(d.endswith(_SURFACED_SUFFIX) for d in r.failures)
    if r.status == "failed" or surfaced:
        return SURFACED
    retried = (any(d.startswith("retry:") for d in r.events(TOOL_DISPATCHED))
               or any(d.startswith("retry:")
                      for d in r.events(MESSAGE_SENT)))
    if retried:
        return RETRIED
    return SWALLOWED


# The probe task the failure census fires each runner at.
_PROBE = "Apply the smallest fix that turns the failing test green."


def failure_behaviour_table(
        runners: dict[str, Runner],
        faults: list[Fault]) -> dict[str, dict[str, str]]:
    """For each runner and fault, the failure-behaviour verdict --- the
    column that repays the exercise.

    A runner that carries an explicit policy (via :func:`attach_policy`) is
    injected under it; one that does not falls back to the dated
    :data:`DISPOSITIONS` policy for its dict-key position. Either way the
    verdict is read back off the OBSERVED faulted run, not the policy.
    """
    table: dict[str, dict[str, str]] = {}
    for name, runner in runners.items():
        if getattr(runner, "fault_policy", None) is None:
            attach_policy(runner, DISPOSITIONS.get(name, {}))
        row: dict[str, str] = {}
        for fault in faults:
            faulted = inject(runner, fault)
            try:
                outcome: RunResult | BaseException = faulted(_PROBE)
            except Exception as exc:      # a framework that raises the fault
                outcome = exc
            row[fault.name] = classify_response(outcome, fault)
        table[name] = row
    return table
