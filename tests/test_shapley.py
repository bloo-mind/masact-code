"""Tests for the Chapter 16 core and Shapley value module."""

import random
from itertools import combinations, permutations
from math import factorial, isclose

from foundations.algorithms.shapley import (
    in_core,
    majority_game,
    shapley,
)


def brute_force_shapley(
    v: dict[frozenset[str], float], agents: list[str]
) -> dict[str, float]:
    """The Shapley value by its definition rather than its closed form:
    average each agent's marginal contribution over all ``n!`` arrival
    orders. Must agree with ``shapley`` on every game."""
    n = len(agents)
    totals = {i: 0.0 for i in agents}
    for order in permutations(agents):
        present: set[str] = set()
        for i in order:
            S = frozenset(present)
            totals[i] += v[S | {i}] - v[S]
            present.add(i)
    return {i: totals[i] / factorial(n) for i in agents}


def random_game(
    agents: list[str], seed: int
) -> dict[frozenset[str], float]:
    """An asymmetric characteristic function: independent random worths on
    every coalition (v of the empty set nought), so no symmetry saves the
    closed form --- it must match the brute force term by term."""
    rng = random.Random(seed)
    v: dict[frozenset[str], float] = {}
    for r in range(len(agents) + 1):
        for S in combinations(agents, r):
            v[frozenset(S)] = 0.0 if r == 0 else round(rng.uniform(0, 100), 4)
    return v


AGENTS = ["coder", "tester", "reviewer"]


def test_majority_game_shares_are_book_values() -> None:
    # The trailing call the chapter prints:
    # shapley(v, agents)
    #   -> {'coder': 100.0, 'tester': 100.0, 'reviewer': 100.0}
    v = majority_game(AGENTS, 300.0)
    assert shapley(v, AGENTS) == {
        "coder": 100.0,
        "tester": 100.0,
        "reviewer": 100.0,
    }


def test_majority_game_characteristic_function() -> None:
    # Any pair takes the whole prize; a lone agent, or nobody, takes nought.
    v = majority_game(AGENTS, 300.0)
    assert v[frozenset()] == 0.0
    assert v[frozenset(["coder"])] == 0.0
    assert v[frozenset(["coder", "tester"])] == 300.0
    assert v[frozenset(AGENTS)] == 300.0


def test_equal_split_not_in_core() -> None:
    # The hundred-apiece division is efficient (sums to v(N) = 300) yet
    # unstable: the coder-tester pair, holding 200, could seize the full 300.
    v = majority_game(AGENTS, 300.0)
    x = {i: 100.0 for i in AGENTS}
    assert sum(x.values()) == v[frozenset(AGENTS)]
    pair = frozenset(["coder", "tester"])
    assert x["coder"] + x["tester"] < v[pair]
    assert not in_core(x, v, AGENTS)


def test_majority_core_is_empty() -> None:
    # No allocation survives: adding the three pair inequalities forces a
    # total of at least 450, but the grand coalition has only 300 to share,
    # so every efficient division fails some pair. Sweep a grid to confirm
    # none of them lands in the core.
    v = majority_game(AGENTS, 300.0)
    steps = range(0, 301, 30)
    found = False
    for a in steps:
        for b in steps:
            c = 300 - a - b
            if c < 0:
                continue
            x = {"coder": float(a), "tester": float(b), "reviewer": float(c)}
            if in_core(x, v, AGENTS):
                found = True
    assert not found


def test_additive_game_has_a_core_allocation() -> None:
    # A game that pays each coalition the sum of its members' worths has a
    # non-empty core: pay each agent exactly its worth and every secession
    # inequality holds with equality.
    worth = {"coder": 120.0, "tester": 90.0, "reviewer": 40.0}
    v = {
        frozenset(S): sum(worth[i] for i in S)
        for r in range(len(AGENTS) + 1)
        for S in combinations(AGENTS, r)
    }
    assert in_core(worth, v, AGENTS)
    # Underpaying an agent breaks its singleton inequality.
    starved = dict(worth)
    starved["coder"] -= 10.0
    starved["tester"] += 10.0
    assert not in_core(starved, v, AGENTS)


def test_closed_form_matches_brute_force_asymmetric() -> None:
    # The n!-orderings average agrees with the closed form on an asymmetric
    # game --- the run checks the transcription of the coefficient, since the
    # two computations share no code.
    v = random_game(AGENTS, seed=16)
    closed = shapley(v, AGENTS)
    brute = brute_force_shapley(v, AGENTS)
    for i in AGENTS:
        assert isclose(closed[i], brute[i], abs_tol=1e-9)


def test_closed_form_matches_brute_force_four_agents() -> None:
    # And it holds beyond three agents, where n! grows past the pairs.
    agents = ["a", "b", "c", "d"]
    v = random_game(agents, seed=44)
    closed = shapley(v, agents)
    brute = brute_force_shapley(v, agents)
    for i in agents:
        assert isclose(closed[i], brute[i], abs_tol=1e-9)


def test_shapley_is_efficient() -> None:
    # Efficiency axiom: the shares sum to the grand coalition's value.
    v = random_game(AGENTS, seed=7)
    phi = shapley(v, AGENTS)
    assert isclose(sum(phi.values()), v[frozenset(AGENTS)], abs_tol=1e-9)
