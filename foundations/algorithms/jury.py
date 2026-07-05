"""Condorcet's jury theorem and its weighted refinement (Chapter 13).

A jury of ``n`` competent, *independent* voters, each right with probability
``p`` above one half, is more likely to be right by majority than any single
member, and approaches certainty as ``n`` grows. This module carries the exact
tail sum the chapter shows, the Nitzan--Paroush optimal weights for *unequal*
jurors, and the correlated-jury ceiling that caps the whole construction once
the independence clause is relaxed.

Standard library only. The arithmetic is exact (``math.comb``); nothing
here is random, so there is nothing to seed.
"""

from math import comb, log

# --- The theorem itself (reproduced verbatim from Chapter 13) --------------


def p_majority(n: int, p: float) -> float:
    return sum(comb(n, k) * p**k * (1 - p) ** (n - k)
               for k in range((n + 1) // 2, n + 1))


# --- Unequal jurors: the Nitzan--Paroush optimal weights -------------------


def weighted_majority_weights(ps: list[float]) -> list[float]:
    """Optimal ballot weights for jurors of competences ``ps``.

    For juror ``i`` of competence ``p_i`` (errors independent), the accuracy-
    maximising rule weights the vote by the log-odds of being right,

        w_i  is proportional to  log(p_i / (1 - p_i)),

    so a juror at ninety per cent outweighs one at sixty several times over,
    and one at fifty is weightless (``log 1 == 0``). Weights are returned
    unnormalised: only their ratios matter to the sign of the weighted count.
    """
    return [log(p / (1 - p)) for p in ps]


# --- The correlated-jury ceiling -------------------------------------------


def effective_jury_size(n: int, rho: float) -> float:
    """Effective number of *independent* jurors when errors correlate.

    Independence is the treacherous clause: shared training, briefings or
    biases correlate the errors that the theorem needs to cancel. Under a
    uniform pairwise error correlation ``rho`` the jury behaves like a smaller
    independent one --- the standard variance-inflation (design-effect)

        n_eff = n / (1 + (n - 1) * rho),

    which reproduces Ladha's headline for the correlated jury: at ``rho = 0``
    all ``n`` votes count, while at ``rho = 1`` a thousand jurors collapse to
    one juror photocopied. The accuracy plateau of an ensemble is this ceiling
    made visible: past the knee, further samples buy a verdict already cast.
    """
    return n / (1 + (n - 1) * rho)
