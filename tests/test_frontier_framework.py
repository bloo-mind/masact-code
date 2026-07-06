"""Hermetic tests for the Chapter 19 framework lab (scorecard + census).

Scripted runners only: no key, no network. The lab's fault mechanism is
exercised by attaching an EXPLICIT policy to a scripted runner --- set
independently of any framework name --- injecting a fault, and asserting the
verdict :func:`classify_response` recovers matches that policy. A wrong
inject or a wrong classify therefore FAILS the test; nothing merely asserts
the module's own dated table back at itself.
"""

from __future__ import annotations

from frontier.framework_lab.scorecard import (
    RETRY, SURFACE, SWALLOW, Fault, attach_policy, classify_response,
    failure_behaviour_table, inject, scorecard,
)
from frontier.runners import scripted_runner

# The three policy actions, mapped to the verdict each must be OBSERVED to
# earn once injected --- the independent ground truth these tests drive from.
_ACTION_VERDICT = {
    SURFACE: "surfaced_cleanly",
    RETRY: "retried_silently",
    SWALLOW: "swallowed",
}


def _runners():
    """Three framework positions, same model (same tokens band) underneath.

    Tokens are held in a narrow band --- the model is fixed --- while the LoC
    table spreads them widely; that gap is the book's headline.
    """
    return {
        "plain": scripted_runner(tokens=180),
        "langgraph": scripted_runner(tokens=220),
        "claude_agent_sdk": scripted_runner(tokens=200),
    }


def test_scorecard_reports_four_columns_and_loc():
    board = scorecard(_runners(), "fix the failing test")
    for cols in board.values():
        for key in ("quality", "tokens", "latency_s", "failures", "loc"):
            assert key in cols
        assert cols["loc"] > 0


def test_loc_spread_dwarfs_token_spread():
    # The book's headline: same model -> modest token spread, but the
    # declaration (LoC) spreads dramatically and misleads.
    board = scorecard(_runners(), "fix the failing test")
    tokens = [c["tokens"] for c in board.values()]
    locs = [c["loc"] for c in board.values()]
    token_ratio = max(tokens) / min(tokens)
    loc_ratio = max(locs) / min(locs)
    assert token_ratio < 1.5
    assert loc_ratio > 3.0
    assert loc_ratio > token_ratio


def test_inject_enacts_each_policy_and_classify_recovers_it():
    # Drive from an INDEPENDENT policy: for each action, attach it to a fresh
    # scripted runner, inject a tool error, and assert classify recovers the
    # action's verdict off the observed run --- a wrong classify FAILS here.
    for action, verdict in _ACTION_VERDICT.items():
        runner = attach_policy(scripted_runner(tokens=200),
                               {Fault.TOOL_ERROR: action})
        res = inject(runner, Fault.TOOL_ERROR)("t")
        assert classify_response(res, Fault.TOOL_ERROR) == verdict


def test_surface_policy_fails_the_run_observably():
    runner = attach_policy(scripted_runner(tokens=200),
                           {Fault.TOOL_ERROR: SURFACE})
    res = inject(runner, Fault.TOOL_ERROR)("t")
    assert res.status == "failed"
    assert res.output == ""
    assert res.failures                       # a visible scar in the columns
    assert classify_response(res, Fault.TOOL_ERROR) == "surfaced_cleanly"


def test_swallow_policy_leaves_no_trace():
    runner = attach_policy(scripted_runner(tokens=200),
                           {Fault.TOOL_ERROR: SWALLOW})
    res = inject(runner, Fault.TOOL_ERROR)("t")
    assert res.status == "shipped"            # columns look spotless...
    assert res.failures == []
    assert not any("fault:" in d for _, d in res.journal)  # ...no trace
    assert classify_response(res, Fault.TOOL_ERROR) == "swallowed"


def test_retry_policy_scars_journal_not_columns():
    runner = attach_policy(scripted_runner(tokens=200),
                           {Fault.TOOL_ERROR: RETRY})
    res = inject(runner, Fault.TOOL_ERROR)("t")
    assert res.status == "shipped"            # clean columns...
    assert res.failures == []
    assert any(d.startswith("retry:")         # ...but a scar in the journal
               for _, d in res.journal)
    assert classify_response(res, Fault.TOOL_ERROR) == "retried_silently"


def test_surface_policy_raises_on_timeout():
    runner = attach_policy(scripted_runner(tokens=200),
                           {Fault.TIMEOUT: SURFACE})
    faulted = inject(runner, Fault.TIMEOUT)
    raised = False
    try:
        faulted("t")
    except TimeoutError as exc:
        raised = True
        assert classify_response(exc, Fault.TIMEOUT) == "surfaced_cleanly"
    assert raised


def test_verdict_follows_policy_not_framework_name():
    # A runner NAMED like the position whose dated assumption SWALLOWs a tool
    # error, but given a SURFACE policy of its own, must classify as surfaced
    # --- proving the verdict tracks observed behaviour, not the name.
    runner = attach_policy(scripted_runner(tokens=200),
                           {Fault.TOOL_ERROR: SURFACE})
    table = failure_behaviour_table({"plain": runner}, [Fault.TOOL_ERROR])
    assert table["plain"]["TOOL_ERROR"] == "surfaced_cleanly"


def test_census_recovers_a_full_independent_policy():
    # Build one runner per action from an INDEPENDENT policy map, run the
    # census, and assert every recovered cell matches the policy that drove
    # it --- the table cannot pass by hardcoding the module's dispositions.
    policy = {
        "surfacer": SURFACE,
        "retrier": RETRY,
        "swallower": SWALLOW,
    }
    runners = {
        name: attach_policy(scripted_runner(tokens=200),
                            {Fault.MALFORMED: action})
        for name, action in policy.items()
    }
    table = failure_behaviour_table(runners, [Fault.MALFORMED])
    for name, action in policy.items():
        assert table[name]["MALFORMED"] == _ACTION_VERDICT[action]


def test_classify_treats_exception_as_clean_surface():
    assert (classify_response(TimeoutError("boom"), Fault.TIMEOUT)
            == "surfaced_cleanly")


def test_untagged_live_position_falls_back_to_dated_disposition():
    # A runner carrying NO explicit policy falls back to the dated
    # DISPOSITIONS assumption for its dict-key position; the census still
    # reads the verdict off the observed run. 'plain' swallows a tool error.
    table = failure_behaviour_table(
        {"plain": scripted_runner(tokens=200)}, [Fault.TOOL_ERROR])
    assert table["plain"]["TOOL_ERROR"] == "swallowed"
