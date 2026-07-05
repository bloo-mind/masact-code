"""Tests for the minimal naming game of Chapter 18."""

import random

from foundations.emergence.naming_game import play, run


def test_population_of_twenty_converges_on_one_shared_word():
    # Within the round cap the population collapses from babel to a
    # single agreed name, and every agent ends holding exactly it.
    word, rounds, converged = run(20, random.Random(0))
    assert converged is True
    assert word is not None
    assert rounds > 0

    result = play(20, random.Random(0))
    assert result.converged is True
    assert result.word == word
    assert len(result.inventories) == 20
    assert all(inv == {word} for inv in result.inventories)


def test_same_seed_gives_identical_results():
    # Determinism: a freshly seeded generator makes a run reproducible.
    assert run(20, random.Random(0)) == run(20, random.Random(0))
    assert run(20, random.Random(7)) == run(20, random.Random(7))

    first = play(20, random.Random(7))
    second = play(20, random.Random(7))
    assert first.word == second.word
    assert first.rounds == second.rounds
    assert first.inventories == second.inventories


def test_different_seeds_pin_their_exact_outcomes():
    # Regression anchors: these are fixed by the seeded interaction
    # sequence and hold across processes (choice is over a sorted
    # inventory, so set hash order cannot perturb them).
    assert run(20, random.Random(0)) == ("w1", 539, True)
    assert run(20, random.Random(7)) == ("w4", 420, True)
    assert run(20, random.Random(42)) == ("w0", 303, True)


def test_a_pair_of_agents_converges():
    # The smallest population: two agents still reach one shared word.
    word, _, converged = run(2, random.Random(1))
    assert converged is True
    result = play(2, random.Random(1))
    assert all(inv == {word} for inv in result.inventories)


def test_cap_reports_non_convergence_without_a_word():
    # Too few rounds to converge: the game reports failure honestly and
    # names no word rather than raising.
    word, rounds, converged = run(20, random.Random(0), max_rounds=1)
    assert converged is False
    assert word is None
    assert rounds == 1
