"""Tests for the Chapter 18 information-cascade module."""

from random import Random

from foundations.emergence.cascade import (
    CASCADE_THRESHOLD,
    Cascade,
    choices_for_signals,
    decide,
    in_cascade,
    simulate,
)


def test_decide_first_agent_follows_its_signal() -> None:
    # With an empty public tally the private signal is all the evidence.
    assert decide(0, 1) == 1
    assert decide(0, 0) == 0


def test_decide_ties_break_towards_the_signal() -> None:
    # One net prior choice exactly cancels an opposing signal; the agent then
    # falls back on its own signal, so a lone choice is still informative.
    assert decide(1, 0) == 0
    assert decide(1, 1) == 1
    assert decide(-1, 1) == 1
    assert decide(-1, 0) == 0


def test_in_cascade_threshold() -> None:
    assert not in_cascade(0)
    assert not in_cascade(1)
    assert not in_cascade(-1)
    assert in_cascade(CASCADE_THRESHOLD)
    assert in_cascade(-CASCADE_THRESHOLD)


def test_cascade_choices_ignore_the_private_signal() -> None:
    # Two aligned early signals lock the tally at +2; from the third agent on
    # the choice no longer depends on the signal drawn. Replaying the same
    # prefix with opposite tails must yield the same tail of choices.
    early = [1, 1]
    choices_a, from_a = choices_for_signals(early + [0, 0, 0, 0])
    choices_b, from_b = choices_for_signals(early + [1, 0, 1, 0])
    assert from_a == 3 and from_b == 3          # herding sets in at agent 3
    assert choices_a == choices_b               # signals stop mattering
    assert choices_a == [1, 1, 1, 1, 1, 1]      # a unanimous up-cascade


def test_two_aligned_signals_start_a_cascade_in_simulation() -> None:
    # The same phenomenon, driven by the seeded sampler rather than by hand.
    # Seed 3 draws two aligned early signals, so herding must set in at the
    # third agent exactly as in the hand-built case above.
    run = simulate(20, 0.7, true_state=1, rng=Random(3))
    assert run.signals[0] == run.signals[1]     # precondition holds
    assert run.formed
    assert run.cascade_from == 3


def test_wrong_cascade_is_possible() -> None:
    # A cascade can harden around the *false* state: the queue converges,
    # confidently and unanimously, on the wrong answer. Such a seed exists.
    true_state = 1
    wrong = None
    for seed in range(2000):
        run = simulate(30, 0.6, true_state, Random(seed))
        if run.wrong_cascade:
            wrong = run
            break
    assert wrong is not None
    assert wrong.formed and not wrong.correct
    assert wrong.choices[-1] == 1 - true_state
    # Everyone from the cascade point on converges on that false state.
    k = wrong.cascade_from
    tail = wrong.choices[k - 1:]
    assert tail and all(c == wrong.choices[-1] for c in tail)


def test_right_cascade_is_also_possible() -> None:
    # The mechanism is not biased against truth: some seeds cascade correctly.
    true_state = 1
    right = None
    for seed in range(2000):
        run = simulate(30, 0.6, true_state, Random(seed))
        if run.formed and run.correct:
            right = run
            break
    assert right is not None
    assert right.choices[-1] == true_state


def test_determinism_under_a_fixed_seed() -> None:
    a = simulate(25, 0.7, true_state=1, rng=Random(12345))
    b = simulate(25, 0.7, true_state=1, rng=Random(12345))
    assert a == b                       # frozen dataclasses compare by value
    assert a.choices == b.choices
    assert a.signals == b.signals


def test_result_shape() -> None:
    run = simulate(10, 0.7, true_state=0, rng=Random(7))
    assert isinstance(run, Cascade)
    assert len(run.choices) == 10
    assert len(run.signals) == 10
    assert all(c in (0, 1) for c in run.choices)
    assert run.formed == (run.cascade_from is not None)
