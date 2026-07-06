"""The capstone scaling lab (Chapter 27): the book's central claim, tested.

Chapter 27 asks the question the whole book has been building towards --- how
many agents, and wired how --- and refuses to answer it by assertion. It runs
one task from the running example across a grid of team *sizes* and
*topologies*, on the same token accounting as the single-agent baseline, and
reads out four curves: quality, tokens, latency, and the failure-mode census.

This package is that instrument. :mod:`~frontier.scaling_lab.sweep` is the
grid and the flat-maximum detector; :mod:`~frontier.scaling_lab.jury` is the
diversity-ablation twin (the jury theorem switching on as jurors decorrelate);
:mod:`~frontier.scaling_lab.run` is the command-line report. The durable
finding is the *method* --- the scaling question is empirical, per task, and
cheap to answer --- not the particular numbers a scripted stand-in prints.
"""

from __future__ import annotations

from .jury import JuryStage, jury_ablation
from .sweep import (
    COUPLED_P,
    PARALLEL_P,
    REGIME_P,
    SIZES,
    TOPOLOGIES,
    compare_to_theory,
    failure_census,
    flat_maximum,
    scaling_scripted_factory,
    scaling_sweep,
)

__all__ = [
    "SIZES", "TOPOLOGIES", "REGIME_P", "PARALLEL_P", "COUPLED_P",
    "scaling_sweep", "flat_maximum", "failure_census",
    "scaling_scripted_factory", "compare_to_theory",
    "JuryStage", "jury_ablation",
]
