"""Sequential information cascades (Chapter 18).

The Bikhchandani--Hirshleifer--Welch model of rational herding. A queue of
agents decide, in turn, between two states of the world. Each holds a single
noisy private signal --- correct with probability ``p > 1/2`` --- and observes
the *public choices*, not the private signals, of everyone ahead of it. Each
does the Bayesian-rational thing: follow its own signal unless the tally of
prior public choices already outweighs it, in which case it discards the
signal and follows the crowd. Once two net choices lean the same way a lone
signal can no longer overturn them, so every subsequent agent copies --- an
*information cascade*. No new information then enters the queue: a thousand
identical choices carry the evidential weight of the first two, and the
cascade may well have locked onto the *wrong* state.

With prior one half and equal signal precision the log-likelihood arithmetic
collapses to counting. Each pre-cascade choice reveals exactly one signal,
worth one unit of evidence, so the public posterior is an integer ``tally``
of net revealed signals and a cascade begins the moment ``abs(tally) >= 2``.
The precision ``p`` therefore governs only how signals are drawn, never the
decision threshold --- a small but telling fact about the model.

Standard library only; all randomness flows through a caller-supplied
``random.Random`` so runs are reproducible.
"""

from dataclasses import dataclass
import random

__all__ = [
    "CASCADE_THRESHOLD",
    "in_cascade",
    "decide",
    "choices_for_signals",
    "Cascade",
    "simulate",
]

# A cascade sets in once the net tally of revealed signals reaches this
# magnitude: a single +/-1 signal can no longer flip a +/-2 public posterior.
CASCADE_THRESHOLD = 2


def in_cascade(tally: int) -> bool:
    """Would an agent facing this public ``tally`` ignore its own signal?"""
    return abs(tally) >= CASCADE_THRESHOLD


def decide(tally: int, s: int) -> int:
    """The Bayesian-rational choice given ``tally`` and private signal ``s``.

    ``s`` and the returned choice are states in ``{0, 1}``. A signal for state
    1 is worth ``+1`` of evidence and one for state 0 ``-1``; the agent picks
    the state its total evidence favours, breaking an exact tie by its own
    signal (which is why the first agent always follows its signal).
    """
    total = tally + (1 if s == 1 else -1)
    if total > 0:
        return 1
    if total < 0:
        return 0
    return s  # a tie leaves the private signal to decide


def choices_for_signals(
    signals: list[int],
) -> tuple[list[int], int | None]:
    """Replay a fixed signal sequence deterministically.

    Returns the public choices and the 1-based index of the agent at which a
    cascade first sets in (``None`` if none does across the whole queue). This
    is the pure core behind :func:`simulate`, with the randomness removed.
    """
    choices: list[int] = []
    cascade_from: int | None = None
    tally = 0
    for i, s in enumerate(signals, start=1):
        if cascade_from is None and in_cascade(tally):
            cascade_from = i
        choices.append(decide(tally, s))
        if not in_cascade(tally):
            tally += 1 if s == 1 else -1  # an informative choice reveals it
    return choices, cascade_from


@dataclass(frozen=True)
class Cascade:
    """The outcome of one sequential run of ``n`` agents."""

    choices: list[int]        # public choices a_1 .. a_n, in order
    signals: list[int]        # the private signals s_1 .. s_n behind them
    true_state: int           # the state the queue was trying to identify
    cascade_from: int | None  # 1-based agent where herding set in, else None

    @property
    def formed(self) -> bool:
        """Did a cascade form at all?"""
        return self.cascade_from is not None

    @property
    def correct(self) -> bool:
        """Did the final choice match the true state?"""
        return bool(self.choices) and self.choices[-1] == self.true_state

    @property
    def wrong_cascade(self) -> bool:
        """A formed cascade that hardened around the *false* state."""
        return self.formed and not self.correct


def simulate(
    n: int, p: float, true_state: int, rng: random.Random
) -> Cascade:
    """Run ``n`` agents deciding in sequence about ``true_state``.

    Each agent's private signal is correct with probability ``p``; ``rng`` (a
    seeded ``random.Random``) supplies every draw, so a fixed seed yields a
    fixed run. The result carries the public ``choices``, whether a cascade
    ``formed``, and where it began.
    """
    signals = [
        true_state if rng.random() < p else 1 - true_state
        for _ in range(n)
    ]
    choices, cascade_from = choices_for_signals(signals)
    return Cascade(choices, signals, true_state, cascade_from)
