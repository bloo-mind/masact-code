"""The shared measurement rig for the frontier labs.

Every lab in this layer reports the same four columns --- quality, tokens,
latency, and failure behaviour --- because the book defines them once and
reuses them: the framework scorecard (Chapter 19), the scaling sweep
(Chapter 27), and the pattern census (Chapter 21) are three instruments over
one rig. A :class:`Runner` turns a task into a :class:`RunResult`; the result
carries the four columns plus an append-only ``journal`` in the Chapter 20
event vocabulary --- because every failure signature the book names is defined
as something legible *in the journal*, not eyeballed in the artefact.

Standard library only; the runners in :mod:`frontier.runners` are the dated
seam where a real framework or vendor SDK plugs in.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

# The Chapter 20 journal vocabulary --- enough of it for the labs to read.
RUN_STARTED = "RunStarted"
MESSAGE_SENT = "MessageSent"
TOOL_DISPATCHED = "ToolDispatched"
TOOL_RETURNED = "ToolReturned"
REVIEWED = "Reviewed"          # detail: "accept: ..." or "reject: ..."
TESTED = "Tested"             # detail: "green" or "red"
AGENT_FINISHED = "AgentFinished"
RUN_FINISHED = "RunFinished"


@dataclass
class RunResult:
    """One measured run: the four columns, plus the journal they are read
    from. ``failures`` holds failure-signature tags a detector raised."""

    task: str
    output: str = ""              # the diff / artefact the run produced
    status: str = "unknown"       # "shipped" | "failed" | "rejected" | ...
    quality: float = 0.0          # a judge's score in [0, 1]
    tokens: int = 0
    latency_s: float = 0.0
    journal: list[tuple[str, str]] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def log(self, event: str, detail: str = "") -> None:
        self.journal.append((event, detail))

    def events(self, name: str) -> list[str]:
        """The details of every journal entry of a given event type."""
        return [detail for event, detail in self.journal if event == name]


Runner = Callable[[str], RunResult]


def run_timed(fn: Callable[[], RunResult]) -> RunResult:
    """Call ``fn`` and stamp the wall-clock latency onto its result."""
    start = time.perf_counter()
    result = fn()
    result.latency_s = time.perf_counter() - start
    return result


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def four_columns(runs: list[RunResult]) -> dict[str, float]:
    """Aggregate a set of runs into the four reporting columns."""
    return {
        "quality": mean([r.quality for r in runs]),
        "tokens": mean([float(r.tokens) for r in runs]),
        "latency_s": mean([r.latency_s for r in runs]),
        "failures": float(sum(len(r.failures) for r in runs)),
    }
