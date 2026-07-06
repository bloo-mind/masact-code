"""Journal detectors: identify each failure from the journal alone (Ch 21).

Chapter 20 insists a failure worth naming is one you can *read in the
journal*, not eyeballed in the artefact. Each detector here takes a
:class:`~frontier.rig.RunResult` and returns ``bool`` after reading only
``r.journal`` / ``r.events(...)`` / ``r.failures`` --- never the artefact and
never ``r.status`` (a green status is exactly what a latent failure hides
behind). The detector *is* the operational definition of the signature.

The one deliberate exception is :func:`is_misroute`. Chapter 21 (@sec-router)
calls the router's misroute *a perfectly healthy run of the wrong kind*:
nothing in the trace is anomalous, because every component behaved, and only
the OUTPUT --- judged by someone who knows what the task needed --- reveals
the miscarriage. So :func:`is_misroute` alone takes an external eval fact (the
correct specialist) and is honestly powerless without it. It is the module's
standing reminder that some failures the journal simply cannot see.

Journal detail format
---------------------
Details are ``"<label>: k1=v1 k2=v2 ..."``. The label names the entry kind
(``routed``, ``tag``, ``plan``, ``replan``, ``dispatch``, ``return``,
``debate``, ``relay``, ``leaf``, ``post``, ``read``); the ``k=v`` tokens carry
the fields a detector reads. Timestamps ride as ``t=<int>`` so a contradiction
can be stated *with a timestamp*; where order alone suffices we use the
journal's own sequence. The injections module writes exactly this format; the
topology runners write healthy instances of it.
"""

from __future__ import annotations

from ..rig import (
    MESSAGE_SENT,
    REVIEWED,
    TOOL_DISPATCHED,
    TOOL_RETURNED,
    RunResult,
)


# --- Detail parsing ------------------------------------------------------

def _label(detail: str) -> str:
    return detail.split(":", 1)[0].strip()


def _kv(detail: str) -> dict[str, str]:
    """Parse the ``k=v`` tokens after the label into a mapping."""
    body = detail.split(":", 1)[1] if ":" in detail else detail
    out: dict[str, str] = {}
    for tok in body.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
    return out


def _ordinal(step: str) -> int:
    """The trailing integer of a step id (``s2`` -> 2); -1 if none."""
    digits = "".join(ch for ch in step if ch.isdigit())
    return int(digits) if digits else -1


def _routed_specialist(r: RunResult) -> str | None:
    """The specialist the router recorded dispatching to (journal-visible ---
    *where* the task went, never *whether* that was right)."""
    for ev, d in r.journal:
        if ev == MESSAGE_SENT and _label(d) == "routed":
            return _kv(d).get("specialist")
    return None


# --- Delegation-family detectors -----------------------------------------

def is_misroute(r: RunResult, correct_specialist: str) -> bool:
    """The one failure the journal cannot see. A misroute is a *perfectly
    healthy run of the wrong kind*: the router dispatched to a real
    specialist, that specialist worked diligently, the tests are green, the
    finish is clean --- nothing in the trace is anomalous, because every
    component behaved. Only the OUTPUT, judged by someone who knows what the
    task actually needed, reveals the miscarriage.

    That knowledge cannot be recovered from ``r.journal``; it is an external
    eval fact, supplied here as ``correct_specialist``. A misroute is simply
    the routed specialist failing to match it. The journal records *where* the
    task went; this argument is the only thing that knows *where it should
    have gone*. No journal-only detector can stand in for it --- which is the
    teaching point (@sec-router): the router has no mechanism for noticing its
    one decision was wrong, so the instrument does not either."""
    routed = _routed_specialist(r)
    if routed is None:
        return False
    return routed != correct_specialist


# A relay whose root-level gap is within this tolerance of the leaf is
# faithful summarisation, not a whisper game: benign rounding or unit drift
# should stay silent. Absolute floor for small leaves; relative for large.
_WHISPER_ABS_TOL = 1.0
_WHISPER_REL_TOL = 0.05


def is_whisper_divergence(r: RunResult) -> bool:
    """Leaf facts and the root's integration claim diverge, the gap widening
    as the claim is relayed up the hierarchy. The deepest ``leaf`` is ground
    truth; each ``relay`` restates a value at a depth; if the error grows
    monotonically toward the root *and* the root-level gap clears a tolerance,
    the whisper game is on. Within tolerance the drift is benign rounding, and
    the detector stays silent --- faithful summarisation is not a failure."""
    leaf: int | None = None
    relays: list[tuple[int, int]] = []
    for ev, d in r.journal:
        f = _kv(d)
        if ev == TOOL_RETURNED and _label(d) == "leaf":
            leaf = int(f["value"])
        elif ev == MESSAGE_SENT and _label(d) == "relay":
            relays.append((int(f["depth"]), int(f["value"])))
    if leaf is None or len(relays) < 2:
        return False
    relays.sort(reverse=True)                 # deepest first, root last
    gaps = [abs(v - leaf) for _, v in relays]
    widening = all(gaps[i] <= gaps[i + 1] for i in range(len(gaps) - 1))
    tol = max(_WHISPER_ABS_TOL, _WHISPER_REL_TOL * abs(leaf))
    return widening and gaps[-1] > gaps[0] and gaps[-1] > tol


# --- Process-family detectors --------------------------------------------

def is_stale_plan(r: RunResult) -> bool:
    """A tool result falsifies a plan step, yet the executor keeps dispatching
    that step (or a later one) on schedule, with no intervening replan --- a
    contradiction the journal ORDER makes plain."""
    falsified: str | None = None
    for ev, d in r.journal:
        lab, f = _label(d), _kv(d)
        if ev == TOOL_RETURNED and "falsifies" in f:
            falsified = f["falsifies"]
        elif ev == MESSAGE_SENT and lab == "replan":
            falsified = None                  # the contradiction is resolved
        elif ev == TOOL_DISPATCHED and falsified is not None:
            step = f.get("step", "")
            if _ordinal(step) >= _ordinal(falsified):
                return True
    return False


def is_placation(r: RunResult) -> bool:
    """Acceptance by politeness, not by correctness. The tempting proxy ---
    the critique growing vaguer while the diff shrinks toward empty --- also
    describes a *healthy* review that converged because its objections were
    resolved; shrinking diffs alone cannot tell the two apart. The real
    discriminator (@sec-reflection-loop: the loop "reports success having
    changed nothing that mattered") is unresolved critique at the moment of
    approval: a review that reaches ``accept`` with objections still OPEN ---
    dropped, not answered. Each ``Reviewed`` entry carries ``open=<n>``, the
    count of objections still standing; a placation is an ``accept`` with
    ``open > 0``."""
    for d in r.events(REVIEWED):
        if not d.startswith("accept"):
            continue
        f = _kv(d)
        if "open" in f and int(f["open"]) > 0:
            return True
    return False


# A polish loop's final diff stays at least this fraction of its first: the
# revisions never approach convergence. A run below the fraction shrank in
# earnest and merely ran out of rounds --- not a polish loop.
_POLISH_CONVERGE_FRACTION = 0.5


def _cycles_after_trend(diffs: list[int]) -> bool:
    """True if a diff size recurs *after* the series stops trending down ---
    the book's "revision five resembling revision three". The initial descent
    does not count; only a value repeating once the shrinking has stalled."""
    stall = len(diffs)
    for i in range(1, len(diffs)):
        if diffs[i] >= diffs[i - 1]:      # the descent has stalled here
            stall = i - 1
            break
    tail = diffs[stall:]
    return len(set(tail)) < len(tail)


def is_polish_loop(r: RunResult) -> bool:
    """Motion without convergence: the round cap is struck and the diffs
    REFUSE to shrink. Two conditions, both from @sec-reflection-loop's "the
    round cap struck, diffs refusing to shrink, and revisions cycling":

    * *non-convergence* --- the final diff is no smaller than a fair fraction
      of the first (a run that shrank steadily and merely hit the cap has
      converged and is NOT a polish loop, however many rounds it took);
    * *cycling* --- a diff size recurs after the downward trend has stalled.
    """
    cap = False
    diffs: list[int] = []
    for ev, d in r.journal:
        if ev == MESSAGE_SENT and _label(d) == "round-cap":
            cap = True
        elif ev == REVIEWED:
            f = _kv(d)
            if "diff" in f:
                diffs.append(int(f["diff"]))
    if not cap or len(diffs) < 3:
        return False
    if diffs[-1] <= _POLISH_CONVERGE_FRACTION * diffs[0]:
        return False                     # shrank in earnest --- converged
    return _cycles_after_trend(diffs)


# --- Collective-family detectors -----------------------------------------

def is_chorus(r: RunResult) -> bool:
    """Positions collapse to one after round one and later rounds add no new
    argument: convergence by conformity, agreement faster than scrutiny."""
    rounds: list[tuple[int, int, int]] = []
    for ev, d in r.journal:
        if ev == MESSAGE_SENT and _label(d) == "debate":
            f = _kv(d)
            rounds.append((int(f["round"]), int(f["stances"]),
                           int(f["newargs"])))
    if len(rounds) < 2:
        return False
    rounds.sort()
    first_stances = rounds[0][1]
    later = [(s, a) for rnd, s, a in rounds if rnd > 1]
    if first_stances < 2 or not later:
        return False
    collapsed = all(s == 1 for s, _ in later)
    no_new = all(a == 0 for _, a in later)
    return collapsed and no_new


def is_stampede(r: RunResult) -> bool:
    """A stampede is not mere fan-out. Healthy parallelism dispatches several
    workers off one posting to do DISTINCT subtasks --- breadth, not waste.
    The pathology the book names (@sec-blackboard: "one juicy posting wakes
    every specialist at once... doing interchangeable work") is *duplication*:
    a burst of near-simultaneous dispatches off one trigger all doing the SAME
    work, so the team pays several times for one follow-up. The discriminator
    is therefore the work target, not the count: three or more consecutive
    same-trigger dispatches whose ``region`` (or, absent that, ``step``) is
    identical --- the same board region / step / tool call, worked in
    parallel by mistake."""
    trigger: str | None = None
    work_counts: dict[str, int] = {}
    for ev, d in r.journal:
        if ev == TOOL_DISPATCHED:
            f = _kv(d)
            trig = f.get("trigger")
            work = f.get("region") or f.get("step", "")
            if trig is not None and trig == trigger:
                work_counts[work] = work_counts.get(work, 0) + 1
            else:
                trigger, work_counts = trig, {work: 1}
            if trigger is not None and work_counts.get(work, 0) >= 3:
                return True
        else:
            trigger, work_counts = None, {}
    return False


def is_stale_read(r: RunResult) -> bool:
    """An artefact reads a version of a key older than a newer posting that
    already predated the read: a stale read on the shared workspace."""
    latest_ver: dict[str, int] = {}
    latest_t: dict[str, int] = {}
    for ev, d in r.journal:
        f = _kv(d)
        if ev == TOOL_RETURNED and _label(d) == "post":
            key, ver, t = f["key"], int(f["ver"]), int(f["t"])
            if ver > latest_ver.get(key, -1):
                latest_ver[key], latest_t[key] = ver, t
        elif ev == MESSAGE_SENT and _label(d) == "read":
            key, rver, rt = f["key"], int(f["ver"]), int(f["t"])
            if (key in latest_ver and latest_ver[key] > rver
                    and latest_t[key] <= rt):
                return True
    return False
