"""A tiny distributed constraint optimisation problem (DCOP) solver.

Chapter 11 sets the optimising form down exactly: agents own variables
``x_1, ..., x_m``, each ranging over a finite domain ``D_i``, and on the
edges ``(i, j)`` of a constraint graph a binary cost function
``f_{ij}: D_i x D_j -> R_{>=0}`` prices every pair of values --- zero for a
pair that fits, rising with the badness of the fit. A solution is a complete
assignment (a value for every variable) minimising the total cost, the sum
over the graph's edges of ``f_{ij}(x_i, x_j)``. The satisfaction problem is
the special case whose solutions are exactly the assignments of cost zero.

Real DCOP is *distributed*: each agent sees only its own variables and the
cost functions on its own edges, and the joint assignment is recovered by
message passing (ABT, ADOPT, DPOP, Max-Sum). This module is deliberately the
undistributed baseline --- one process with the whole graph in view, solving
the small instances the book uses exactly by branch-and-bound --- so the
optimum a distributed protocol should reach is on hand to compare against.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

Value = Any                          # a domain element: a colour, a route...
Edge = frozenset[str] | tuple[str, str]
Cost = Callable[[Value, Value], float]


@dataclass
class Dcop:
    """A DCOP instance held whole in one process.

    ``variables`` maps each variable ``x_i`` to its finite domain ``D_i``.
    ``costs`` maps an edge to its cost function ``f_{ij}``: give the edge as
    a ``frozenset({i, j})`` when the cost is symmetric, or as an ordered
    ``(i, j)`` tuple, in which case ``f`` is applied as ``f(x_i, x_j)`` in
    that order --- the only way to price an asymmetric constraint.
    """

    variables: dict[str, list[Value]]
    costs: dict[Edge, Cost]


def total_cost(dcop: Dcop, assignment: dict[str, Value]) -> float:
    """The objective at a complete assignment: the sum over the graph's
    edges of ``f_{ij}(x_i, x_j)``."""
    total = 0
    for edge, f in dcop.costs.items():
        i, j = tuple(edge)           # order kept for tuples; symmetric else
        total += f(assignment[i], assignment[j])
    return total


def solve(dcop: Dcop) -> tuple[dict[str, Value] | None, float]:
    """Return a least-cost complete assignment and its cost.

    The search is branch-and-bound over the variables in insertion order:
    a partial assignment is extended one variable at a time, each extension
    charged only for the edges it completes, and a branch is pruned the
    moment its cost reaches the best complete assignment found so far. Exact
    and exhaustive but pruned --- meant for Chapter 11's small graphs, not
    for scale. Returns ``(None, inf)`` if no complete assignment exists.
    """
    order = list(dcop.variables)
    pos = {v: k for k, v in enumerate(order)}

    # Charge each edge when its later-in-order endpoint is assigned, by which
    # point both endpoints have values; keep the (a, b) order f expects.
    triggers: dict[str, list[tuple[str, str, Cost]]] = {v: [] for v in order}
    for edge, f in dcop.costs.items():
        if isinstance(edge, frozenset):
            a, b = sorted(edge, key=pos.__getitem__)
        else:
            a, b = edge
        later = a if pos[a] > pos[b] else b
        triggers[later].append((a, b, f))

    best: dict[str, Value] | None = None
    best_cost: float = math.inf
    assign: dict[str, Value] = {}

    def search(k: int, cost: float) -> None:
        nonlocal best, best_cost
        if k == len(order):
            best, best_cost = dict(assign), cost
            return
        v = order[k]
        for value in dcop.variables[v]:
            assign[v] = value
            step = sum(f(assign[a], assign[b]) for a, b, f in triggers[v])
            if cost + step < best_cost:          # branch-and-bound: prune
                search(k + 1, cost + step)
        assign.pop(v, None)                      # backtrack

    search(0, 0)
    return best, best_cost
