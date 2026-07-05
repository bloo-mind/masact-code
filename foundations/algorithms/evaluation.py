"""Paired comparison for stochastic-system evaluation (Chapter 24).

Two systems --- a team ``A`` and a strong single agent ``B`` --- are run on
the *same* ``K`` tasks, and their quality scores compared *per task*, so that
task difficulty (usually the largest noise source by far) cancels in each
difference ``d_k = q_k^A - q_k^B`` instead of drowning the signal. The paired
``t`` statistic is the mean difference over its standard error: a large value
is evidence that the two systems are genuinely distinguishable rather than two
draws from one urn.

Standard library only (``statistics``); the arithmetic is deterministic, so
there is nothing to seed.
"""

from statistics import mean, stdev


def paired_t(q_a: list[float], q_b: list[float]) -> dict[str, float]:
    """Paired ``t`` statistic for per-task quality scores ``q_a``, ``q_b``.

    Returns the mean difference ``mean_d``, its standard error ``se`` (the
    standard deviation ``s_d`` of the differences over ``sqrt(K)``), and their
    ratio ``t``. Reproduced from the Chapter 24 listing: on that chapter's toy
    scores for ``K = 6`` tasks it gives ``mean_d`` 0.032, ``se`` 0.014 and
    ``t`` 2.3 --- suggestive on ``K - 1 = 5`` degrees of freedom, evidence
    rather than a settled fact.

    Identical scores carry no signal: with zero variance there is nothing to
    divide by, so ``t`` is reported as nil rather than raising.
    """
    d = [a - b for a, b in zip(q_a, q_b)]
    K = len(d)
    s_d = stdev(d)
    if s_d == 0.0:  # zero variance: a nil statistic, not a divide-by-zero
        return {"mean_d": mean(d), "se": 0.0, "t": 0.0}
    t = mean(d) / (s_d / K**0.5)
    return {"mean_d": mean(d), "se": s_d / K**0.5, "t": t}
