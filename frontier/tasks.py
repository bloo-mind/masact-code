"""A batch of repository issues of graded difficulty --- the labs' workload.

The scaling lab (Chapter 27) runs the sweep on one *parallel* task and one
*coupled* one, because the flat maximum sits at a different team size in each
regime. The framework lab (Chapter 19) runs a single bounded coding job. Every
issue is self-contained --- the buggy function and its failing test are on the
page --- so a capable model can propose a verifiable fix, and a scripted
stand-in can score it with no model at all.

``regime`` and ``parallelism`` are the levers the scaling model reads: a
parallel task divides cleanly across workers (high ``p``), a coupled one does
not, so adding workers buys coordination cost rather than speed (low ``p``).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Issue:
    """A self-contained repository issue: the bug and its failing test."""

    id: str
    prompt: str
    difficulty: str          # "easy" | "medium" | "hard"
    regime: str              # "parallel" | "coupled"
    parallelism: float       # p in the Amdahl-with-tax model (0..1)


def _bug(name: str, code: str, test: str) -> str:
    return (f"The helper `{name}` is buggy:\n    {code}\n"
            f"It fails the test `{test}`. Propose the smallest fix.")


# --- The parallel batch: independent issues, one per worker ---------------

ISSUE_BATCH: list[Issue] = [
    Issue("first-word", _bug(
        "first_word",
        "def first_word(s): return s.split()[0]",
        "assert first_word('   ') == ''"),
        "easy", "parallel", 0.9),
    Issue("head", _bug(
        "head",
        "def head(xs): return xs[0]",
        "assert head([]) is None"),
        "easy", "parallel", 0.9),
    Issue("clamp", _bug(
        "clamp",
        "def clamp(x, lo, hi): return max(hi, min(lo, x))",
        "assert clamp(5, 0, 10) == 5"),
        "medium", "parallel", 0.9),
    Issue("safe-div", _bug(
        "safe_div",
        "def safe_div(a, b): return a / b",
        "assert safe_div(1, 0) is None"),
        "medium", "parallel", 0.9),
    Issue("last", _bug(
        "last",
        "def last(xs): return xs[-1]",
        "assert last([]) is None"),
        "hard", "parallel", 0.9),
]


# --- The coupled task: interdependent parts, resists division -------------

COUPLED_TASK = Issue(
    "rename-api", (
        "Rename the method `size()` to `length()` across a module and every "
        "call site, keeping it consistent. The signature change and the "
        "call sites constrain one another --- no part can be fixed alone."),
    "hard", "coupled", 0.3)


def parallel_task() -> list[Issue]:
    """The parallel regime: the whole graded batch, one issue per worker."""
    return list(ISSUE_BATCH)


def coupled_task() -> Issue:
    """The coupled regime: a single change whose parts do not separate."""
    return COUPLED_TASK
