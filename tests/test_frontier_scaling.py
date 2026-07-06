"""Hermetic tests for the capstone scaling lab (Chapter 27).

No key, no network: every runner is the scripted stand-in, and every number
is exact. The tests put the book's three scaling hypotheses --- flat maximum,
cost outrunning quality, failures migrating to the joins --- and the
jury-ablation twin to their own standard of evidence.
"""

from __future__ import annotations

from foundations.algorithms.scaling import speedup

from frontier.scaling_lab import (
    REGIME_P,
    SIZES,
    TOPOLOGIES,
    compare_to_theory,
    failure_census,
    flat_maximum,
    jury_ablation,
    scaling_scripted_factory,
    scaling_sweep,
)
from frontier.scaling_lab.sweep import _flat_argmax


def _sweep(regime: str) -> dict:
    return scaling_sweep(scaling_scripted_factory(regime))


def test_flat_maximum_earlier_for_coupled_than_parallel():
    # Hypothesis (a): the coupled task's flat maximum sits at a smaller team
    # size than the parallel one's, for every topology.
    coupled = _sweep("coupled")
    parallel = _sweep("parallel")
    for topo in TOPOLOGIES:
        assert flat_maximum(coupled, topo) < flat_maximum(parallel, topo)


def _grid_argmax(p: float, kappa: float) -> int:
    # The theory's maximiser over the *empirical* grid, computed here
    # independently of the module under test.
    return max(SIZES, key=lambda n: speedup(n, p, kappa))


def test_compare_to_theory_matches_grid_argmax_across_kappa():
    # The sweep recovers the theory's grid maximum for *any* kappa, not just
    # a single tuned point. The expected value is derived here from speedup
    # over SIZES, independently of what compare_to_theory computes.
    for regime in ("coupled", "parallel"):
        p = REGIME_P[regime]
        for kappa in (0.005, 0.01, 0.02, 0.05):
            expected = _grid_argmax(p, kappa)
            cmp = compare_to_theory(regime, kappa)
            assert cmp["theoretical_nstar"] == expected
            assert cmp["empirical_nstar"] == expected


def test_flat_maximum_is_true_argmax_on_non_monotone_series():
    # A plateau that only rises after it (the case a rise-until-it-stops walk
    # under-reports): the flat maximum must be the true argmax, not the first
    # plateau. Sizes [1, 2, 4, 8] with capability [0.5, 0.5, 0.9, 0.95] -> 8.
    assert _flat_argmax([1, 2, 4, 8], [0.5, 0.5, 0.9, 0.95]) == 8
    assert _flat_argmax([1, 2, 4, 8], [0.5, 0.9, 0.9, 0.95]) == 8
    # A genuinely non-monotone curve peaking in the middle: argmax at n=2,
    # tie-broken to the smallest size on the tie at the tail.
    assert _flat_argmax([1, 2, 4, 8], [0.5, 0.95, 0.8, 0.95]) == 2


def test_tokens_keep_rising_past_the_flat_maximum():
    # Hypothesis (b): cost outruns quality. Tokens at the largest team exceed
    # tokens at the flat maximum, for every topology and regime.
    for regime in ("coupled", "parallel"):
        sweep = _sweep(regime)
        for topo in TOPOLOGIES:
            n_star = flat_maximum(sweep, topo)
            top = max(SIZES)
            assert sweep[(top, topo)]["tokens"] > sweep[(n_star, topo)][
                "tokens"]


def test_failure_census_migrates_competence_to_join():
    # Hypothesis (c): the census flips from competence- to join-dominated as
    # the population grows.
    factory = scaling_scripted_factory("parallel")
    small = failure_census([factory(1, t)(task="") for t in TOPOLOGIES])
    large = failure_census([factory(8, t)(task="") for t in TOPOLOGIES])

    small_join = (small["specification"] + small["handoff"]
                  + small["verification"])
    large_join = (large["specification"] + large["handoff"]
                  + large["verification"])

    assert small["competence"] > small_join   # size 1: competence-dominated
    assert large_join > large["competence"]    # size 8: join-dominated
    # And the join family is genuinely spread, not one label.
    assert sum(1 for k in ("specification", "handoff", "verification")
               if large[k] > 0) >= 2


def test_jury_accuracy_rises_as_correlation_falls():
    # The twin: decorrelating the panel lifts accuracy monotonically while the
    # estimated error-correlation falls monotonically.
    stages = jury_ablation()
    accuracies = [s.accuracy for s in stages]
    correlations = [s.correlation for s in stages]
    disagreements = [s.disagreement for s in stages]

    assert all(b > a for a, b in zip(accuracies, accuracies[1:]))
    assert all(b < a for a, b in zip(correlations, correlations[1:]))
    assert all(b > a for a, b in zip(disagreements, disagreements[1:]))
    # The fully split panel is the most accurate rung of the ladder.
    assert stages[-1].accuracy == max(accuracies)


def test_jury_rho_is_a_measured_estimate_not_an_identity():
    # rho_hat must be *measured* from a simulation, so it approximates but
    # does not equal the design rho on the intermediate rungs. The design
    # rho is recomputed here from n and the effective size, independently.
    n = 7
    stages = jury_ablation(n=n)
    design_rho = [(n - s.effective_n) / (s.effective_n * (n - 1))
                  for s in stages]
    # It genuinely recovers the design value (within sampling tolerance) ...
    assert all(abs(s.correlation - r) < 0.02
               for s, r in zip(stages, design_rho))
    # ... but is not the exact algebraic identity: at least one intermediate
    # rung carries measurable sampling noise.
    assert any(abs(s.correlation - r) > 1e-6
               for s, r in zip(stages, design_rho))


def test_jury_ablation_is_reproducible_under_its_seed():
    # Seeded simulation: two runs at the same seed agree exactly; a different
    # seed moves the noisy estimate.
    a = [s.correlation for s in jury_ablation(seed=1)]
    b = [s.correlation for s in jury_ablation(seed=1)]
    c = [s.correlation for s in jury_ablation(seed=2)]
    assert a == b
    assert a != c
