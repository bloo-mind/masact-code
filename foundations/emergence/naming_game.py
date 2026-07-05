"""The minimal naming game: a shared vocabulary with no designer.

Chapter 18 exhibits the naming game as emergence caught in the act ---
it grows Chapter 11's conventions *without* Chapter 11's designer. A
population of agents each keep a private inventory of words for one
object, all inventories empty to begin with. On each interaction a
random *speaker* utters a word (inventing a fresh one if its inventory
is empty) to a random *hearer*. If the hearer already knows the word
the interaction *succeeds* and both collapse their inventories to that
single word; otherwise it *fails* and the hearer merely adds the word.
Nobody legislates, nobody announces, yet the population undergoes a
sharp transition from babel to one agreed name --- a convention with no
committee (Baronchelli et al., 2006).

This is a classical, dependency-free model: it does not touch the
Chapter 20 runtime. Randomness is seeded so a run is reproducible, and
word choice is made over a *sorted* inventory rather than a raw set so
the sequence is deterministic across processes as well as within one.
"""

import random
from dataclasses import dataclass, field

# A generous safety cap; the minimal game converges far below it for the
# small populations of Chapter 18 (tens of agents, hundreds of rounds).
DEFAULT_MAX_ROUNDS = 100_000


@dataclass
class Result:
    """The outcome of one naming-game run.

    ``word`` is the name the whole population settled on, or ``None`` if
    it had not converged when ``rounds`` reached the cap. ``inventories``
    is each agent's final word memory --- at convergence every one of
    them is the singleton ``{word}``.
    """

    word: str | None
    rounds: int
    converged: bool
    inventories: list[set[str]] = field(default_factory=list)


def _consensus(inventories: list[set[str]]) -> str | None:
    """The single word every agent now holds, or ``None`` if the
    population has not yet collapsed onto one shared name."""
    first = inventories[0]
    if len(first) != 1:
        return None
    (w,) = first
    return w if all(inv == {w} for inv in inventories) else None


def play(
    n_agents: int,
    rng: random.Random,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> Result:
    """Run the minimal naming game and return the full final state.

    Agents are ``0 .. n_agents - 1`` (two or more). ``rng`` (a seeded
    ``random.Random``) supplies every draw, so a fixed seed yields a
    reproducible run. Each round draws a distinct speaker and hearer
    uniformly at random; the speaker utters a word from its inventory,
    coining a fresh one if empty; a success collapses both inventories to
    that word, a failure teaches it to the hearer. Consensus can only
    arise the moment an interaction succeeds, so it is tested only then
    --- the loop stops as soon as every agent holds the same lone word.
    """
    inventories: list[set[str]] = [set() for _ in range(n_agents)]
    minted = 0                          # fresh-word counter: w0, w1, ...
    for r in range(1, max_rounds + 1):
        s, h = rng.sample(range(n_agents), 2)
        if inventories[s]:
            w = rng.choice(sorted(inventories[s]))
        else:
            w = f"w{minted}"            # invent a name for the object
            minted += 1
            inventories[s].add(w)       # the coiner keeps its coinage
        if w in inventories[h]:         # success: both drop all but w
            inventories[s] = {w}
            inventories[h] = {w}
            shared = _consensus(inventories)
            if shared is not None:
                return Result(shared, r, True, inventories)
        else:                           # failure: the hearer learns w
            inventories[h].add(w)
    return Result(None, max_rounds, False, inventories)


def run(
    n_agents: int,
    rng: random.Random,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> tuple[str | None, int, bool]:
    """The headline result: ``(converged_word, rounds, converged)``.

    A thin wrapper over :func:`play` that drops the final inventories.
    """
    result = play(n_agents, rng, max_rounds)
    return result.word, result.rounds, result.converged
