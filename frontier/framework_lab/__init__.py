"""The Chapter 19 framework lab: one job, several framework positions.

One bounded coding job is built across framework positions and scored on
four columns --- tokens, latency, lines of code, and failure behaviour ---
with the same model held underneath. The exported surface is the scorecard,
the fault vocabulary, and the failure-behaviour table.
"""

from __future__ import annotations

from .scorecard import (
    DISPOSITIONS, LOC, RETRY, SURFACE, SWALLOW, Fault, attach_policy,
    classify_response, failure_behaviour_table, inject, scorecard,
)

__all__ = [
    "LOC", "DISPOSITIONS", "Fault", "scorecard", "inject",
    "classify_response", "failure_behaviour_table", "attach_policy",
    "SURFACE", "RETRY", "SWALLOW",
]
