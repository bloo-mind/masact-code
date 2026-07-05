"""Tests for the Chapter 24 evaluation module."""

from foundations.algorithms.evaluation import paired_t


def test_book_toy_example() -> None:
    # The chapter's toy scores for K = 6 tasks, and the three trailing
    # values the listing prints (# -> 0.032, # -> 0.014, # -> 2.3).
    q_a = [0.82, 0.74, 0.91, 0.63, 0.78, 0.85]  # team, per task
    q_b = [0.79, 0.70, 0.88, 0.66, 0.71, 0.80]  # strong single agent
    result = paired_t(q_a, q_b)
    assert round(result["mean_d"], 3) == 0.032
    assert round(result["se"], 3) == 0.014
    assert round(result["t"], 2) == 2.3


def test_pairing_cancels_task_difficulty() -> None:
    # Raw scores wander across a quarter of the scale; the differences
    # scatter by only a few hundredths --- the cancellation at work.
    q_a = [0.82, 0.74, 0.91, 0.63, 0.78, 0.85]
    q_b = [0.79, 0.70, 0.88, 0.66, 0.71, 0.80]
    result = paired_t(q_a, q_b)
    assert result["mean_d"] > 0  # the team leads on average
    assert result["se"] < 0.05


def test_identical_inputs_give_zero_t() -> None:
    # Zero variance is handled without dividing by zero: no signal, no t.
    q = [0.5, 0.6, 0.7, 0.4, 0.9, 0.8]
    result = paired_t(q, q)
    assert result["mean_d"] == 0.0
    assert result["se"] == 0.0
    assert result["t"] == 0.0
