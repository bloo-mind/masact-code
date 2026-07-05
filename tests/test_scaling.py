"""Tests for the Chapter 1 Amdahl-for-agents speedup model."""

from foundations.algorithms.scaling import (
    best_team_size, ceiling, speedup,
)


def test_speedup_book_value():
    # The book prints ``round(speedup(8, ...), 2)  # -> 3.72``.
    assert round(speedup(8, 0.9, 0.002), 2) == 3.72


def test_best_team_size_book_value():
    # The book prints ``max(range(1, 101), ...)  # -> 8``.
    assert best_team_size(0.9, 0.002) == 8


def test_ceiling_is_tax_free_limit():
    # 1 / (1 - p): the ten-fold ceiling for p = 0.9. In binary
    # floating point 1 / (1 - 0.9) is 10.000000000000002, so we
    # compare the tax-free limit to 10 up to representation error.
    assert round(ceiling(0.9), 9) == 10


def test_best_team_size_matches_brute_force():
    p, kappa, upper = 0.9, 0.002, 100
    brute = max(range(1, upper + 1),
                key=lambda n: speedup(n, p, kappa))
    assert best_team_size(p, kappa, upper) == brute


def test_zero_tax_peaks_at_upper_bound():
    # With no coordination tax the speedup rises monotonically,
    # so the finite maximiser sits at the upper bound.
    assert best_team_size(0.9, 0.0) == 100
    assert best_team_size(0.9, 0.0, upper=50) == 50


def test_ceiling_bounds_the_peak():
    # Even the best team stays below the tax-free ceiling.
    n_star = best_team_size(0.9, 0.002)
    assert speedup(n_star, 0.9, 0.002) < ceiling(0.9)


def test_single_agent_speedup_is_one():
    # One agent pays no tax and earns no parallel gain: S(1) = 1.
    assert speedup(1, 0.9, 0.002) == 1.0
