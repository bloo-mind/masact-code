"""The architectural-patterns lab (Chapter 21).

Chapter 21 argues that a multi-agent architecture is a *catalogue choice*,
and that each pattern in the catalogue fails in its own characteristic way ---
a signature that is legible *in the journal* (Chapter 20's event vocabulary),
not eyeballed in the artefact. This lab is that argument made runnable:

* :mod:`~frontier.patterns.catalogue` --- the nine patterns in three families,
  the three anti-patterns, and three scripted topology runners for the
  pattern-swap.
* :mod:`~frontier.patterns.signatures` --- journal *detectors*: each names
  one failure, read from the journal alone.
* :mod:`~frontier.patterns.injections` --- break each pattern its own way, so
  the paired detector fires.
* :mod:`~frontier.patterns.compose` --- composition voids warranties: two
  compositions, each with a new failure mode neither pattern has alone.

Standard library only; every path is hermetic (no key, no network).
"""

from .catalogue import (
    CATALOGUE,
    Family,
    Pattern,
    debate_run,
    peer_run,
    supervisor_run,
)

__all__ = [
    "CATALOGUE", "Family", "Pattern",
    "supervisor_run", "peer_run", "debate_run",
]
