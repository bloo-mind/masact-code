"""Tests for the Chapter 23 dependability cores.

The module carries book-level demonstration state (``seen``, ``faults``,
``journal``) at module scope, so each test resets it, and every test
neutralises the real backoff by monkeypatching ``time.sleep`` to a no-op.
"""

import pytest

from foundations.algorithms import dependability
from foundations.algorithms.dependability import (
    approve,
    charge_card,
    deliver,
    run_to_gate,
)


@pytest.fixture(autouse=True)
def reset_state(monkeypatch: pytest.MonkeyPatch) -> None:
    # Instant tests: the backoff sleep is real in production, a no-op here.
    monkeypatch.setattr(dependability.time, "sleep", lambda *a, **k: None)
    # Reset the module-level demonstration state in place (deliver/approve
    # look these names up in module globals at call time).
    dependability.seen.clear()
    dependability.journal.clear()
    dependability.faults[:] = [TimeoutError("gateway slow")]


def test_deliver_retries_transient_then_caches() -> None:
    # One transient fault, then success; a second delivery of the same key
    # is served from the cache and the effect does not run a second time.
    box = [TimeoutError("gateway slow")]   # one transient Heisenbug
    completed = {"n": 0}

    def effect() -> str:
        if box:
            raise box.pop()                # transient failure on attempt 0
        completed["n"] += 1                # count only full completions
        return "charged 1500p"

    assert deliver("pay-1", effect) == "charged 1500p"   # retry lands
    assert deliver("pay-1", effect) == "charged 1500p"   # from cache
    assert completed["n"] == 1             # the effect ran exactly once
    assert dependability.seen["pay-1"] == "charged 1500p"


def test_deliver_idempotency_key_runs_effect_once() -> None:
    # No transient fault at all: the sole point under test is that the
    # keyed effect fires once and the duplicate is a dictionary lookup.
    runs = {"n": 0}

    def effect() -> str:
        runs["n"] += 1
        return "sent"

    assert deliver("msg-7", effect) == "sent"
    assert deliver("msg-7", effect) == "sent"
    assert runs["n"] == 1


def test_deliver_exhausts_retries_and_raises() -> None:
    # Every attempt fails (a retry-proof Bohrbug): deliver raises rather
    # than returning, leaving the caller a failure to route, not a silence.
    def always_times_out() -> str:
        raise TimeoutError("gateway slow")

    with pytest.raises(TimeoutError, match="retries exhausted: doomed"):
        deliver("doomed", always_times_out, n=3)


def test_book_deliver_arrow_values() -> None:
    # The chapter's two printed calls, byte-for-byte:
    #   deliver("pay-42", charge_card)  # -> 'charged 1500p' (one retry)
    #   deliver("pay-42", charge_card)  # -> 'charged 1500p' (from cache)
    assert deliver("pay-42", charge_card) == "charged 1500p"
    assert deliver("pay-42", charge_card) == "charged 1500p"


def test_gate_parks_then_deploys() -> None:
    # run_to_gate('release') -> 'parked' and logs ApprovalRequested;
    # approve('release') then yields 'deployed release'.
    assert run_to_gate("release") == "parked"
    assert ("ApprovalRequested", "release") in dependability.journal
    assert approve("release") == "deployed release"
    assert ("ApprovalGranted", "release") in dependability.journal


def test_book_gate_arrow_values() -> None:
    # The chapter's two printed calls, byte-for-byte:
    #   run_to_gate("release-v2")  # -> 'parked'
    #   approve("release-v2")      # -> 'deployed release-v2'
    assert run_to_gate("release-v2") == "parked"
    assert approve("release-v2") == "deployed release-v2"


def test_gate_park_survives_arbitrary_delay() -> None:
    # A park is only a fold that has not been resumed yet: parking twice
    # before approval logs the request but never deploys.
    assert run_to_gate("ship") == "parked"
    assert run_to_gate("ship") == "parked"
    asked = [e for e in dependability.journal
             if e[0] == "ApprovalRequested"]
    assert ("ApprovalGranted", "ship") not in dependability.journal
    assert approve("ship") == "deployed ship"
    assert len(asked) == 2
