"""Contract Net protocol (Smith, 1980) as a small, self-contained
simulation of Chapter 10's announce--bid--award--report cycle.

A *manager* with a task to place does not simply order a worker to comply.
It *announces* the task; contractors weigh it against their own situation
and *bid* a numeric cost --- lower is better --- or decline; the manager
*awards* the contract to the lowest bidder; the winner *executes* and
reports success or failure; and on failure the manager *reassigns* to the
next-best available bidder, until one succeeds or the field is exhausted.

The contractors here are benevolent, as Chapter 10 assumes: a bid is an
honest statement of fitness, not a strategic move to win the award. Failure
is modelled two ways --- a contractor may be intrinsically unreliable (or
fail at random on its own seeded generator), or its name may be listed in
``inject_failures`` to force the reassignment path for a test.

This module is deliberately self-contained and does not import the Chapter
20 runtime. There the announce/bid/award/report exchange travels as
``Message`` objects carrying ``Performative`` speech acts --- REQUEST
announces, PROPOSE bids, ACCEPT awards, DONE and ERROR report; here the
control flow stays in plain Python so the protocol itself remains visible.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import random
from typing import Protocol


class Contractor(Protocol):
    """An agent that may bid on a task and, if awarded it, execute it."""

    name: str

    def bid(self, task: str) -> float | None:
        """Return a cost to undertake ``task``, or ``None`` to decline."""
        ...

    def execute(self, task: str) -> bool:
        """Attempt the awarded task; return whether it succeeded."""
        ...


@dataclass
class Bidder:
    """A deterministic contractor: a fixed cost and a fixed reliability."""

    name: str
    cost: float | None            # ``None`` declines the announcement
    reliable: bool = True         # whether ``execute`` reports success

    def bid(self, task: str) -> float | None:
        return self.cost

    def execute(self, task: str) -> bool:
        return self.reliable


@dataclass
class FlakyBidder:
    """A contractor that fails at random, on its own seeded generator."""

    name: str
    cost: float
    fail_prob: float
    rng: random.Random

    def bid(self, task: str) -> float | None:
        return self.cost

    def execute(self, task: str) -> bool:
        return self.rng.random() >= self.fail_prob


@dataclass
class Bid:
    """One contractor's response to an announcement."""

    contractor: Contractor
    cost: float


@dataclass
class Award:
    """The result of a round: who completed the task, and how it went."""

    contractor: Contractor | None   # the contractor that succeeded, if any
    succeeded: bool
    attempts: tuple[str, ...]       # names tried, in award order


def collect_bids(task: str,
                 contractors: Iterable[Contractor]) -> list[Bid]:
    """Announce ``task`` and gather bids, dropping those who decline."""
    bids = []
    for c in contractors:
        cost = c.bid(task)
        if cost is not None:
            bids.append(Bid(c, cost))
    return bids


def announce_award(
    manager_task: str,
    contractors: Sequence[Contractor],
    inject_failures: Iterable[str] = (),
) -> Award:
    """Run one Contract Net round, reassigning on failure.

    Contractors are ranked by ascending bid --- lowest cost wins, ties keep
    input order. Each is awarded in turn and asked to execute; a contractor
    whose name is in ``inject_failures``, or whose ``execute`` returns
    ``False``, is treated as having failed, and the task passes to the
    next-best bidder. If every bidder fails, the round ends in a clean
    failure rather than an exception.
    """
    forced = set(inject_failures)
    ranked = sorted(collect_bids(manager_task, contractors),
                    key=lambda b: b.cost)
    attempts: list[str] = []
    for bid in ranked:
        c = bid.contractor
        attempts.append(c.name)
        if c.name not in forced and c.execute(manager_task):
            return Award(c, True, tuple(attempts))
    return Award(None, False, tuple(attempts))


def demo(seed: int = 0) -> Award:
    """A round where the cheapest bidder is flaky and reassignment saves
    the task: an idle agent declines, ``cheap`` draws a failure on seed 0,
    and ``steady`` completes the work."""
    rng = random.Random(seed)
    contractors: list[Contractor] = [
        Bidder("idle", cost=None),                 # declines to bid
        FlakyBidder("cheap", cost=2.0, fail_prob=0.9, rng=rng),
        Bidder("steady", cost=5.0),
    ]
    return announce_award("compile the report", contractors)
