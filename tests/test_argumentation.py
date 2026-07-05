"""Tests for Chapter 14's Dung grounded extension."""

from foundations.algorithms.argumentation import (
    grounded, is_admissible, is_conflict_free,
)

# The four-node review-thread framework of section 14.4: the patch
# argument P, the reviewer's objection R, the coder's rebuttal B, and the
# tester's trace T, with R attacking P, B attacking R, and T attacking B.
A = {'P', 'R', 'B', 'T'}
R_attacks = {('R', 'P'), ('B', 'R'), ('T', 'B')}


def test_grounded_reinstates_the_objection():
    # The trace and the objection stand; the rebuttal and patch fall.
    assert grounded(A, R_attacks) == {'T', 'R'}


def test_grounded_climbs_from_the_empty_set():
    # A framework whose only unattacked argument is its whole verdict.
    assert grounded({'x'}, set()) == {'x'}
    assert grounded({'a', 'b'}, {('a', 'b')}) == {'a'}


def test_grounded_is_empty_under_mutual_attack():
    # Two arguments attacking each other force no one; the cautious
    # extension accepts nothing.
    assert grounded({'a', 'b'}, {('a', 'b'), ('b', 'a')}) == set()


def test_conflict_free_accepts_the_grounded_extension():
    assert is_conflict_free({'T', 'R'}, R_attacks) is True


def test_conflict_free_rejects_a_set_holding_an_attack():
    # B attacks R, so {R, B} contains an argument with its own attacker.
    assert is_conflict_free({'R', 'B'}, R_attacks) is False


def test_conflict_free_of_the_empty_set():
    assert is_conflict_free(set(), R_attacks) is True


def test_admissible_accepts_the_grounded_extension():
    assert is_admissible({'T', 'R'}, A, R_attacks) is True


def test_admissible_rejects_an_undefended_set():
    # {R} alone is conflict-free but cannot defend R against B.
    assert is_admissible({'R'}, A, R_attacks) is False


def test_admissible_rejects_a_conflicting_set():
    # {R, B} is not even conflict-free, so it cannot be admissible.
    assert is_admissible({'R', 'B'}, A, R_attacks) is False


def test_empty_set_is_admissible():
    assert is_admissible(set(), A, R_attacks) is True
