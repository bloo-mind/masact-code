"""The core and the Shapley value for coalitional games (Chapter 16).

A coalitional game is one characteristic function ``v``: a map from every
coalition ``S`` (a ``frozenset`` of agents) to the value it can guarantee by
cooperating internally, with ``v`` of the empty set nought. On that object sit
the chapter's two instruments of division. The *core* is stability --- the
allocations no sub-coalition would secede from --- and it can be empty. The
*Shapley value* ``phi`` is fairness, axiomatised: each agent's marginal
contribution averaged over the ``n!`` orders in which the team might assemble,
the unique rule satisfying efficiency, symmetry, the null-player property, and
additivity.

The ``shapley`` function below is reproduced verbatim from @sec-core-shapley
so a reader copying from the book finds the identical code here. Standard
library only; the arithmetic is exact factorial bookkeeping, so nothing is
random and there is nothing to seed.
"""

from itertools import combinations
from math import factorial, isclose

# Allocations are computed with floating division of factorials, so equality
# and secession tests carry a small tolerance rather than demanding the bit.
_TOL = 1e-9


# --- The Shapley value (reproduced verbatim from Chapter 16) ---------------


def shapley(v: dict[frozenset[str], float],
            agents: list[str]) -> dict[str, float]:
    n = len(agents)
    phi = {}
    for i in agents:
        rest = [j for j in agents if j != i]
        phi[i] = sum(
            factorial(s) * factorial(n - s - 1) / factorial(n)
            * (v[S | {i}] - v[S])
            for s in range(n)
            for S in map(frozenset, combinations(rest, s)))
    return phi


# --- The characteristic function of the majority game ----------------------


def majority_game(
    agents: list[str], prize: float
) -> dict[frozenset[str], float]:
    """The chapter's simple-majority game: any two agents can take the whole
    ``prize``, a lone agent nothing. Returns ``v`` over every coalition ---
    ``prize`` for coalitions of size two or more, nought otherwise --- the
    game whose core @sec-core-shapley proves empty."""
    return {frozenset(S): prize if len(S) >= 2 else 0.0
            for r in range(len(agents) + 1)
            for S in combinations(agents, r)}


# --- The core membership test ----------------------------------------------


def in_core(
    x: dict[str, float],
    v: dict[frozenset[str], float],
    agents: list[str],
) -> bool:
    """Whether allocation ``x`` lies in ``core(v)``: it must share out exactly
    the grand coalition's value and pay every coalition at least its outside
    worth. That is one budget equality, ``sum_i x_i == v(N)``, and the ``2^n``
    secession inequalities ``sum_{i in S} x_i >= v(S)`` for all ``S``."""
    if set(x) != set(agents):   # an outsider cannot balance the books
        return False
    grand = frozenset(agents)
    if not isclose(sum(x.values()), v[grand], abs_tol=_TOL):
        return False
    for r in range(len(agents) + 1):
        for S in map(frozenset, combinations(agents, r)):
            paid = sum(x[i] for i in S)
            if paid < v[S] and not isclose(paid, v[S], abs_tol=_TOL):
                return False
    return True
