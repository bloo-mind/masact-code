"""Amdahl's law for agents: the coordination-tax speedup model.

Chapter 1 prices the trade of adding agents. One agent finishes a task
in time T1 (normalised to 1); a fraction ``p`` of the work is genuinely
parallelisable, so ``n`` agents shrink it to ``p / n``, while keeping
one another informed levies a coordination tax ``c(n) = kappa n(n-1)/2``
that grows with the wiring rather than the work. The speedup

    S(n) = T1 / T(n),   T(n) = (1 - p) + p / n + c(n),

rises only while each new agent removes more waiting than its talking
adds, so it peaks at a finite team size ``n*`` --- the maximiser
:func:`best_team_size` locates. Were the talking free, the speedup would
merely approach the tax-free ceiling ``1 / (1 - p)``.

British English throughout; standard library only.
"""


def speedup(n: int, p: float, kappa: float) -> float:
    c = kappa * n * (n - 1) / 2       # the coordination tax
    return 1 / ((1 - p) + p / n + c)  # T1 normalised to 1


def best_team_size(p: float, kappa: float, upper: int = 100) -> int:
    """Return the finite maximiser n* over team sizes 1..upper."""
    return max(range(1, upper + 1), key=lambda n: speedup(n, p, kappa))


def ceiling(p: float) -> float:
    """Return the tax-free speedup limit 1 / (1 - p), as n grows."""
    return 1 / (1 - p)
