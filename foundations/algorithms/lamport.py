"""Lamport logical clocks and circular-wait detection (Chapter 11).

A logical clock manufactures an order the agents do not share: each keeps
one integer counter, ticks it on every event, stamps the counter onto each
outgoing message, and on receipt advances past the stamp before ticking.
The numbering respects Lamport's *happens-before* relation --- if ``a``
happens before ``b`` then ``C(a) < C(b)`` --- without any shared clock.

``tick`` and ``recv`` are the two module-level functions the book prints;
``LamportClock`` wraps a per-process counter around them as an
object-oriented convenience. ``has_deadlock`` tests Coffman's circular-wait
condition: a cycle in the wait-for graph, the one Coffman condition that,
denied, makes deadlock impossible.
"""

from dataclasses import dataclass
from enum import Enum

__all__ = ["tick", "recv", "LamportClock", "has_deadlock"]


def tick(c: int) -> int:              # every event ticks the counter
    return c + 1


def recv(c: int, stamp: int) -> int:  # a receipt lands past the stamp
    return tick(max(c, stamp))


@dataclass
class LamportClock:
    """A single agent's logical clock: one integer, ticked per event."""

    c: int = 0

    def tick(self) -> int:
        # a local event advances the counter
        self.c = tick(self.c)
        return self.c

    def send(self) -> int:
        # a send is an event; the new counter stamps the message
        return self.tick()

    def recv(self, stamp: int) -> int:
        # a receipt leaps past the stamp, then ticks
        self.c = recv(self.c, stamp)
        return self.c


class _Mark(Enum):
    WHITE = 0   # unvisited
    GREY = 1    # on the current search path
    BLACK = 2   # fully explored


def has_deadlock(wait_for: dict[str, set[str]]) -> bool:
    """True iff the wait-for graph holds a cycle (circular wait).

    ``wait_for`` maps each agent to the set of agents it is blocked on. A
    back-edge to a grey vertex --- one still on the current search path ---
    closes a cycle, and a cycle is a circular chain of waiting: deadlock.
    """
    mark: dict[str, _Mark] = {}

    def visit(a: str) -> bool:
        mark[a] = _Mark.GREY
        for b in wait_for.get(a, ()):
            m = mark.get(b, _Mark.WHITE)
            if m is _Mark.GREY:
                return True
            if m is _Mark.WHITE and visit(b):
                return True
        mark[a] = _Mark.BLACK
        return False

    return any(
        mark.get(a, _Mark.WHITE) is _Mark.WHITE and visit(a)
        for a in wait_for
    )
