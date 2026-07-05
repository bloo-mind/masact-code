"""Calibrated trust: Brier scores and reliability diagrams (Chapter 26).

An agent is *calibrated* when its stated confidence means what it says: of
the claims it makes at ninety per cent confidence, about ninety per cent are
true. This module carries the two instruments Chapter 26 embeds verbatim ---
the Brier score, the mean squared gap between confidence and outcome, and the
reliability diagram's per-bucket (stated, observed) pairs --- so a reader
copying the listing from the book finds the identical code here. Around them
sits the one summary number the chapter leaves to the companion repository:
the expected calibration error, the reliability sag weighted by traffic.

Confidences are carried as the list ``f`` and outcomes (one if the claim was
correct, zero if not) as the list ``o``, matching the book's ``f_i`` and
``o_i``. Standard library only; nothing here is random, so there is nothing
to seed.
"""

# --- The instruments (reproduced verbatim from Chapter 26) -----------------


def brier(f: list[float], o: list[int]) -> float:
    return sum((f_i - o_i) ** 2 for f_i, o_i in zip(f, o)) / len(f)

def reliability(f: list[float], o: list[int],
                buckets: int = 10) -> list[tuple[float, float]]:
    bins = [[] for _ in range(buckets)]
    for f_i, o_i in zip(f, o):
        bins[min(int(f_i * buckets), buckets - 1)].append((f_i, o_i))
    return [(sum(f_i for f_i, _ in b) / len(b),    # stated
             sum(o_i for _, o_i in b) / len(b))    # observed
            for b in bins if b]


# --- The reliability diagram summarised as one number ----------------------


def ece(f: list[float], o: list[int], buckets: int = 10) -> float:
    """Expected calibration error: the sag, weighted by traffic.

    The reliability diagram's per-bucket gaps collapsed to a single number
    --- the mean of ``|stated - observed|`` across the non-empty buckets,
    each weighted by the share of claims it holds,

        ECE = sum_b (|b| / N) * |stated_b - observed_b|,

    so a wide gap in a rarely used bucket counts for little and a narrow one
    on the agent's busiest confidence counts for much. It is zero for the
    perfectly calibrated and rises towards one as self-report and reality
    part company --- the Brier score's companion, reported beside the diagram.
    """
    n = len(f)
    bins = [[] for _ in range(buckets)]
    for f_i, o_i in zip(f, o):
        bins[min(int(f_i * buckets), buckets - 1)].append((f_i, o_i))
    return sum(len(b) / n
               * abs(sum(f_i for f_i, _ in b) / len(b)
                     - sum(o_i for _, o_i in b) / len(b))
               for b in bins if b)
