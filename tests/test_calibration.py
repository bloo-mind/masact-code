"""Tests for the Chapter 26 calibration module."""

import random

from foundations.algorithms.calibration import brier, ece, reliability

# The book's overconfident record: ten claims at "ninety", five at "sixty",
# with seven and two respectively coming true.
f = [0.9] * 10 + [0.6] * 5
o = [1] * 7 + [0] * 3 + [1] * 2 + [0] * 3


def test_book_arrow_values() -> None:
    # The two trailing calls the chapter prints (# -> 0.26 and the pairs).
    assert brier(f, o) == 0.26
    assert reliability(f, o) == [(0.6, 0.4), (0.9, 0.7)]


def test_brier_bounds_and_landmarks() -> None:
    # Omniscience scores zero; confident-and-wrong scores one.
    assert brier([1.0, 0.0], [1, 0]) == 0.0
    assert brier([1.0, 0.0], [0, 1]) == 1.0
    # Unwavering hedging at one half earns 0.25 --- the score of saying
    # nothing --- and the book's bravado lands a shade worse.
    assert brier([0.5] * 4, [1, 0, 1, 0]) == 0.25
    assert brier(f, o) > 0.25


def test_reliability_sag_is_below_the_diagonal() -> None:
    # Each pair sits twenty points under the diagonal: the stable sag.
    for stated, observed in reliability(f, o):
        assert observed < stated
        assert round(stated - observed, 10) == 0.2


def test_ece_measures_the_sag() -> None:
    # Both buckets sag by exactly 0.2, so their traffic-weighted mean is 0.2.
    assert round(ece(f, o), 10) == 0.2


def test_ece_zero_for_perfectly_calibrated_record() -> None:
    # A record where each confidence bucket comes true at exactly its stated
    # rate hugs the diagonal: no sag anywhere, so the error is exactly zero.
    f = [0.9] * 10 + [0.6] * 10 + [0.2] * 10
    o = ([1] * 9 + [0] * 1) + ([1] * 6 + [0] * 4) + ([1] * 2 + [0] * 8)
    assert ece(f, o) == 0.0


def test_ece_near_zero_for_well_calibrated_generator() -> None:
    # Draw many claims whose outcomes are genuinely Bernoulli(f); the observed
    # frequency converges on the stated confidence, so the error tends to
    # nought. Seeded so the assertion is deterministic.
    rng = random.Random(26)
    confidences = [0.1, 0.3, 0.5, 0.7, 0.9]
    f = [c for c in confidences for _ in range(4000)]
    o = [1 if rng.random() < f_i else 0 for f_i in f]
    assert ece(f, o) < 0.02
