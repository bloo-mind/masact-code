"""Tests for the tiny DCOP solver of Chapter 11."""

import itertools
import math

from foundations.algorithms.dcop import Dcop, solve, total_cost


def _clash(a: object, b: object) -> int:
    # Graph-colouring cost: 1 when adjacent variables share a value, else 0.
    return 1 if a == b else 0


def _triangle(colours: list[str]) -> Dcop:
    return Dcop(
        variables={"x1": colours, "x2": colours, "x3": colours},
        costs={
            frozenset({"x1", "x2"}): _clash,
            frozenset({"x2", "x3"}): _clash,
            frozenset({"x1", "x3"}): _clash,
        },
    )


def test_triangle_two_colours_has_min_cost_one():
    # A triangle is not 2-colourable, so some edge must clash: cost 1.
    dcop = _triangle(["red", "green"])
    assignment, cost = solve(dcop)
    assert cost == 1
    assert set(assignment) == {"x1", "x2", "x3"}
    assert total_cost(dcop, assignment) == 1


def test_single_edge_two_colours_has_min_cost_zero():
    # Two variables joined by one edge: colour them apart, cost 0.
    colours = ["red", "green"]
    dcop = Dcop(
        variables={"x1": colours, "x2": colours},
        costs={frozenset({"x1", "x2"}): _clash},
    )
    assignment, cost = solve(dcop)
    assert cost == 0
    assert assignment["x1"] != assignment["x2"]


def test_triangle_three_colours_is_satisfiable():
    # With a third colour a proper colouring exists: cost 0.
    _, cost = solve(_triangle(["r", "g", "b"]))
    assert cost == 0


def test_ordered_tuple_edge_preserves_argument_order():
    # An asymmetric cost: zero only for the ordered pair (x1, x2) == (0, 1).
    def only_zero_one(a: int, b: int) -> int:
        return 0 if (a, b) == (0, 1) else 1

    dcop = Dcop(
        variables={"x1": [0, 1], "x2": [0, 1]},
        costs={("x1", "x2"): only_zero_one},
    )
    assignment, cost = solve(dcop)
    assert cost == 0
    assert assignment == {"x1": 0, "x2": 1}


def test_branch_and_bound_matches_brute_force():
    # Pruned search must return the same optimum as scoring every assignment.
    colours = ["a", "b", "c"]
    variables = {v: colours for v in ("x1", "x2", "x3", "x4")}
    edges = [("x1", "x2"), ("x2", "x3"), ("x3", "x4"),
             ("x4", "x1"), ("x1", "x3")]
    dcop = Dcop(variables=variables,
                costs={frozenset(e): _clash for e in edges})
    _, cost = solve(dcop)
    brute = min(
        total_cost(dcop, dict(zip(variables, combo)))
        for combo in itertools.product(*variables.values())
    )
    assert cost == brute


def test_empty_problem_has_the_empty_assignment_at_zero_cost():
    assignment, cost = solve(Dcop(variables={}, costs={}))
    assert assignment == {}
    assert cost == 0


def test_unsolvable_when_a_domain_is_empty():
    dcop = Dcop(variables={"x1": ["red"], "x2": []},
                costs={frozenset({"x1", "x2"}): _clash})
    assignment, cost = solve(dcop)
    assert assignment is None
    assert math.isinf(cost)
