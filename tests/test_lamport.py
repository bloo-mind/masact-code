"""Tests for the Chapter 11 Lamport clock and circular-wait detector."""

from foundations.algorithms.lamport import (
    LamportClock, has_deadlock, recv, tick,
)


def test_book_demo_functions():
    # Reproduces the book's printed demo byte-for-byte.
    coder, reviewer = 2, 0
    C_a = coder = tick(coder)
    C_b = reviewer = recv(reviewer, C_a)
    assert (C_a, C_b, C_a < C_b) == (3, 4, True)


def test_tick_and_recv_pieces():
    assert tick(2) == 3            # every event ticks the counter
    assert recv(0, 3) == 4        # leap past the stamp, then tick
    assert recv(5, 3) == 6        # local counter already ahead of stamp


def test_clock_class_matches_functions():
    # The class is a per-process wrapper around tick/recv.
    coder = LamportClock(2)
    reviewer = LamportClock(0)
    C_a = coder.send()            # send is an event: ticks and stamps
    C_b = reviewer.recv(C_a)      # receipt leaps past the stamp
    assert C_a == 3
    assert C_b == 4
    assert C_a < C_b
    assert coder.c == 3


def test_clock_default_starts_at_zero():
    clock = LamportClock()
    assert clock.c == 0
    assert clock.tick() == 1
    assert clock.tick() == 2


def test_deadlock_on_two_cycle():
    wait_for = {"a": {"b"}, "b": {"a"}}
    assert has_deadlock(wait_for) is True


def test_no_deadlock_on_chain():
    wait_for = {"a": {"b"}, "b": {"c"}, "c": set()}
    assert has_deadlock(wait_for) is False


def test_no_deadlock_on_empty_graph():
    assert has_deadlock({}) is False


def test_deadlock_on_three_cycle():
    wait_for = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
    assert has_deadlock(wait_for) is True


def test_no_deadlock_on_diamond_dag():
    # Two paths converge but nothing points back: no circular wait.
    wait_for = {
        "a": {"b", "c"}, "b": {"d"}, "c": {"d"}, "d": set(),
    }
    assert has_deadlock(wait_for) is False


def test_self_loop_is_deadlock():
    # An agent waiting on itself is a degenerate circular wait.
    assert has_deadlock({"a": {"a"}}) is True
