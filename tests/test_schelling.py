"""Tests for Chapter 18's Schelling segregation model."""

import random

from foundations.emergence.schelling import (
    Grid,
    Kind,
    is_content,
    random_grid,
    run,
    same_kind_fraction,
    segregation,
    step,
)


def test_low_tolerance_segregates_well_above_the_random_baseline():
    # A seeded random mix sits near the 0.5 baseline; sweeping with a low
    # tolerance (content even as a minority) still tips it into stark
    # segregation --- the parable's whole point.
    rng = random.Random(42)
    grid = random_grid(30, 30, 0.1, rng)
    assert segregation(grid) < 0.6
    run(grid, 0.3, rng, sweeps=100)
    assert segregation(grid) > 0.7


def test_zero_tolerance_leaves_everyone_content_so_nothing_moves():
    rng = random.Random(0)
    grid = random_grid(20, 20, 0.1, rng)
    before = dict(grid.cells)
    assert step(grid, 0.0, rng) == 0
    assert grid.cells == before
    # ``run`` therefore halts after one no-move sweep.
    assert run(grid, 0.0, rng, sweeps=100) == 1
    assert grid.cells == before


def test_run_reaches_a_fixed_point_before_the_cap():
    rng = random.Random(42)
    grid = random_grid(30, 30, 0.1, rng)
    sweeps = run(grid, 0.3, rng, sweeps=100)
    assert sweeps < 100                  # stopped at a fixed point
    assert step(grid, 0.3, rng) == 0     # and it is genuinely fixed


def test_checkerboard_centre_is_half_same_kind():
    # The eight Moore neighbours split four same (diagonals), four other.
    cells = {(r, c): (Kind.A if (r + c) % 2 == 0 else Kind.B)
             for r in range(3) for c in range(3)}
    grid = Grid(3, 3, cells)
    assert same_kind_fraction(grid, 1, 1) == 0.5


def test_is_content_uses_a_greater_or_equal_threshold():
    # Centre A with two same and two other neighbours: fraction 0.5.
    grid = Grid(3, 3, {
        (1, 1): Kind.A,
        (0, 0): Kind.A, (0, 1): Kind.A,
        (2, 1): Kind.B, (2, 2): Kind.B,
    })
    assert same_kind_fraction(grid, 1, 1) == 0.5
    assert is_content(grid, 1, 1, 0.5)          # boundary is content
    assert not is_content(grid, 1, 1, 0.51)


def test_uniform_block_is_fully_segregated_and_frozen():
    grid = Grid(2, 2, {(0, 0): Kind.A, (0, 1): Kind.A,
                       (1, 0): Kind.A, (1, 1): Kind.A})
    assert segregation(grid) == 1.0
    assert step(grid, 1.0, random.Random(0)) == 0


def test_isolated_agent_is_content_and_absent_from_segregation():
    grid = Grid(3, 3, {(0, 0): Kind.A})
    assert is_content(grid, 0, 0, 1.0)          # nobody to object to
    assert same_kind_fraction(grid, 0, 0) == 0.0
    assert segregation(grid) == 0.0             # no occupied neighbours


def test_discontented_agent_relocates_to_an_empty_cell():
    # One A marooned among B's is discontented at tolerance 0.5 and must
    # move to the grid's only empty cell, (0, 2).
    grid = Grid(2, 3, {
        (0, 0): Kind.A,
        (0, 1): Kind.B, (1, 0): Kind.B,
        (1, 1): Kind.B, (1, 2): Kind.B,
    })
    assert step(grid, 0.5, random.Random(0)) == 1
    assert (0, 0) not in grid.cells             # vacated
    assert grid.cells[(0, 2)] is Kind.A         # relocated


def test_empties_lists_every_unoccupied_cell():
    grid = Grid(2, 2, {(0, 0): Kind.A})
    assert set(grid.empties()) == {(0, 1), (1, 0), (1, 1)}


def test_random_grid_respects_density_and_even_split():
    rng = random.Random(1)
    grid = random_grid(10, 10, 0.2, rng)
    assert len(grid.cells) == 80                # 20% of 100 left empty
    a = sum(k is Kind.A for k in grid.cells.values())
    assert a == 40                             # even split of the 80
