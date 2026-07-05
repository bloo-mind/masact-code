"""Schelling's segregation model on a bounded square grid.

Chapter 18's first parable, rendered as a small runnable model. Two kinds
of agent, ``A`` and ``B``, occupy cells of a grid and the rest are empty.
An agent is *content* when the fraction of its *occupied* Moore neighbours
sharing its kind is at least ``tolerance`` --- a low bar, since an agent
may be content even as a local minority. A discontented agent relocates to
a randomly chosen empty cell. Sweeping these moves to a fixed point drives
a randomly mixed grid, whose same-kind neighbour fraction starts near a
half, into stark segregation: a macro-outcome far more extreme than the
mild micro-preference demanded, which is the whole point of the parable ---
even a low tolerance, happy as a minority, still segregates.

Every source of randomness is seeded through ``random.Random`` so that runs
reproduce exactly. Standard library only. British English throughout.
"""

import random
from dataclasses import dataclass, field
from enum import Enum


class Kind(Enum):
    """The two kinds of agent; an empty cell holds neither."""

    A = "A"
    B = "B"


# The eight Moore-neighbourhood offsets; the grid does not wrap at its edges.
_MOORE = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
          if (dr, dc) != (0, 0)]


@dataclass
class Grid:
    """A ``rows`` by ``cols`` grid. ``cells`` maps each occupied coordinate
    ``(r, c)`` to its kind; any coordinate absent from ``cells`` is empty."""

    rows: int
    cols: int
    cells: dict[tuple[int, int], Kind] = field(default_factory=dict)

    def empties(self) -> list[tuple[int, int]]:
        """Every coordinate not currently occupied, in row-major order."""
        return [(r, c) for r in range(self.rows) for c in range(self.cols)
                if (r, c) not in self.cells]


def _fraction(grid: Grid, r: int, c: int) -> float | None:
    """The same-kind fraction over the occupied Moore neighbours of the
    agent at ``(r, c)``, or ``None`` when it has no occupied neighbour."""
    mine = grid.cells[(r, c)]
    total = same = 0
    for dr, dc in _MOORE:
        other = grid.cells.get((r + dr, c + dc))
        if other is not None:
            total += 1
            same += other is mine
    return same / total if total else None


def same_kind_fraction(grid: Grid, r: int, c: int) -> float:
    """The same-kind fraction over occupied neighbours; ``0.0`` for an
    agent with no occupied neighbour (its fraction is undefined)."""
    f = _fraction(grid, r, c)
    return 0.0 if f is None else f


def is_content(grid: Grid, r: int, c: int, tolerance: float) -> bool:
    """Whether the agent at ``(r, c)`` is content: its same-kind fraction
    reaches ``tolerance``. An agent with no occupied neighbour has nobody to
    object to and counts as content."""
    f = _fraction(grid, r, c)
    return f is None or f >= tolerance


def segregation(grid: Grid) -> float:
    """The model's order parameter: the mean same-kind neighbour fraction
    over occupied cells. A random two-kind mix sits near ``0.5``; a
    segregated grid approaches ``1.0``. Isolated occupied cells carry no
    fraction and are left out of the mean; ``0.0`` if none qualify."""
    fractions = [
        f for (r, c) in grid.cells
        if (f := _fraction(grid, r, c)) is not None
    ]
    return sum(fractions) / len(fractions) if fractions else 0.0


def step(grid: Grid, tolerance: float, rng: random.Random) -> int:
    """One relocation sweep, mutating ``grid`` in place. The agents that are
    discontented at the start of the sweep are taken in row-major order, and
    each moves to an empty cell drawn by ``rng``; every move frees one cell
    and fills another, so the pool of empties stays current as the sweep
    runs. Returns the number of relocations made."""
    discontented = [
        (r, c) for (r, c) in sorted(grid.cells)
        if not is_content(grid, r, c, tolerance)
    ]
    moves = 0
    for (r, c) in discontented:
        empties = grid.empties()
        if not empties:
            break
        target = rng.choice(empties)
        grid.cells[target] = grid.cells.pop((r, c))
        moves += 1
    return moves


def run(grid: Grid, tolerance: float, rng: random.Random,
        sweeps: int = 100) -> int:
    """Sweep to a fixed point --- a sweep in which no agent moves --- or
    until the cap ``sweeps`` is reached, whichever comes first, mutating
    ``grid`` in place. Returns the number of sweeps actually performed."""
    for t in range(sweeps):
        if step(grid, tolerance, rng) == 0:
            return t + 1
    return sweeps


def random_grid(rows: int, cols: int, empty_fraction: float,
                rng: random.Random) -> Grid:
    """A fresh grid with a fraction ``empty_fraction`` of cells left empty
    and the rest split as evenly as possible between the two kinds, every
    placement drawn from the seeded generator ``rng``."""
    coords = [(r, c) for r in range(rows) for c in range(cols)]
    rng.shuffle(coords)
    n_empty = round(empty_fraction * len(coords))
    occupied = coords[n_empty:]
    half = len(occupied) // 2
    cells = {p: Kind.A for p in occupied[:half]}
    cells.update({p: Kind.B for p in occupied[half:]})
    return Grid(rows=rows, cols=cols, cells=cells)
