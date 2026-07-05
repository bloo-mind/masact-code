"""Sealed-bid auctions and the Gode--Sunder zero-intelligence market.

Small, transparent renderings of the mechanisms of Chapter 15. The
sealed-bid rules take a mapping from bidder name to bid ``b_i`` and
return the winner and its price; ``best_response_second_price``
demonstrates Vickrey's result that bidding one's value ``v_i`` weakly
dominates every alternative; and ``zi_double_auction`` reproduces the
Gode--Sunder finding that budget-constrained *random* traders extract
near-full surplus, the institution supplying the intelligence the
agents lack. Standard library only. British English throughout.
"""

import random


def second_price(bids: dict[str, float]) -> tuple[str, float]:
    """Award the good to the highest bidder at the highest price
    among the *others'* envelopes -- the Vickrey rule."""
    winner = max(bids, key=bids.get)
    others = [b for name, b in bids.items() if name != winner]
    price = max(others) if others else 0.0
    return winner, price


def first_price(bids: dict[str, float]) -> tuple[str, float]:
    """Award the good to the highest bidder at its own bid."""
    winner = max(bids, key=bids.get)
    return winner, bids[winner]


def _payoff(value: float, b_i: float, others: list[float]) -> float:
    """Bidder i's second-price payoff against a fixed field: the
    surplus ``v_i - m`` when the bid ``b_i`` tops the highest rival
    bid ``m``, and nothing otherwise."""
    m = max(others) if others else 0.0
    return value - m if b_i > m else 0.0


def best_response_second_price(
    value: float, others: list[float]
) -> bool:
    """Confirm that bidding one's value is a best response under the
    second-price rule: no alternative bid earns more against this
    field. The payoff jumps only at the pivotal ``m``, so a grid
    straddling ``m`` and the value witnesses the weak dominance."""
    m = max(others) if others else 0.0
    truthful = _payoff(value, value, others)
    grid = {0.0, m, value, m - 1.0, m + 1.0, value - 1.0,
            value + 1.0, (value + m) / 2.0, max(value, m) + 1.0}
    return all(
        truthful >= _payoff(value, b_i, others)
        for b_i in grid if b_i >= 0.0
    )


def _max_surplus(
    buyer_values: list[float], seller_costs: list[float]
) -> float:
    """Surplus of the competitive matching: pair the keenest buyers
    with the cheapest sellers while a gain from trade survives.
    Allocative surplus depends only on *which* traders clear, so the
    sorted pairing bounds every possible allocation."""
    v = sorted(buyer_values, reverse=True)
    c = sorted(seller_costs)
    total = 0.0
    for v_i, c_j in zip(v, c):
        if v_i <= c_j:                 # no gain left to capture
            break
        total += v_i - c_j
    return total


def zi_double_auction(
    buyer_values: list[float],
    seller_costs: list[float],
    rounds: int,
    seed: int,
) -> float:
    """Gode--Sunder zero-intelligence continuous double auction.

    Each active buyer posts a random bid in ``[0, v_i]`` and each
    active seller a random ask in ``[c_j, hi]`` -- the sole
    discipline the budget constraint that forbids bidding above one's
    value or asking below one's cost. The keenest crossing pair (the
    highest bid meeting the lowest ask) trades and leaves the market.
    Returns allocative efficiency: realised surplus over the maximum
    surplus of the competitive matching.
    """
    rng = random.Random(seed)
    buyers = list(buyer_values)
    sellers = list(seller_costs)
    hi = max(buyers + sellers)
    realised = 0.0
    for _ in range(rounds):
        if not buyers or not sellers:
            break
        bids = [(rng.uniform(0.0, v), i)
                for i, v in enumerate(buyers)]
        asks = [(rng.uniform(c, hi), j)
                for j, c in enumerate(sellers)]
        b_i, i = max(bids)             # keenest buyer this round
        a_j, j = min(asks)             # keenest seller this round
        if b_i >= a_j:                 # the bid crosses the ask
            realised += buyers[i] - sellers[j]
            buyers.pop(i)
            sellers.pop(j)
    denom = _max_surplus(buyer_values, seller_costs)
    return realised / denom if denom else 1.0
