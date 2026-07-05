"""Tests for the Chapter 13 jury module."""

from foundations.algorithms.jury import (
    effective_jury_size,
    p_majority,
    weighted_majority_weights,
)


def test_book_arrow_values() -> None:
    # The two trailing calls the chapter prints (# -> 0.648, # -> 0.979...).
    assert round(p_majority(3, 0.6), 3) == 0.648
    assert round(p_majority(101, 0.6), 3) == 0.979


def test_competence_amplifies() -> None:
    # Above one half, aggregation sharpens: the majority beats a single juror.
    assert p_majority(101, 0.6) > 0.6


def test_incompetence_also_amplifies() -> None:
    # The dark twin: with p below one half, the majority is worse than one
    # juror --- aggregation is an amplifier, not a purifier.
    p = 0.4
    assert p_majority(3, p) < p
    assert p_majority(101, p) < p


def test_perfect_juror_and_coin() -> None:
    assert p_majority(9, 1.0) == 1.0
    assert round(p_majority(101, 0.5), 3) == 0.5


def test_nitzan_paroush_orders_by_competence() -> None:
    weights = weighted_majority_weights([0.9, 0.6])
    # The abler juror earns the larger ballot.
    assert weights[0] > weights[1]
    # A coin-flip juror is weightless.
    assert weighted_majority_weights([0.5]) == [0.0]


def test_correlated_jury_ceiling() -> None:
    # Independent jurors all count; perfectly correlated ones collapse to one.
    assert effective_jury_size(1000, 0.0) == 1000
    assert effective_jury_size(1000, 1.0) == 1.0
    # Correlation taxes the count: fewer effective jurors than heads present.
    assert effective_jury_size(1000, 0.1) < 1000
