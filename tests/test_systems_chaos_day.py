"""The chaos-day finale is itself a test (Chapter 23, the assembled system).

Each injection returns a boring/surprising verdict; a surprise is a defect in
the dependability machinery, so the whole day reduces to one assertion. These
run the real LangGraph team on a scripted brain, so they skip without the
systems extra.
"""

import pytest

pytest.importorskip("langgraph")

from systems.coding_team import chaos_day  # noqa: E402


def test_every_injection_is_boring():
    verdicts = chaos_day.run_chaos_day()
    assert len(verdicts) == 6
    assert all(verdicts)


@pytest.mark.parametrize("injection", chaos_day.INJECTIONS,
                         ids=[f.__name__ for f in chaos_day.INJECTIONS])
def test_injection_holds(injection):
    # each failure class is met by its designed response, in isolation
    assert injection() is True
