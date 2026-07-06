"""Hermetic tests for the interoperability lab (Chapter 22).

Every test runs offline: the MCP round-trip uses the in-memory transport, so
no subprocess and no network are needed. The ``mcp`` package is required for
the tool-altitude tests, so those are guarded with ``importorskip``.
"""

from __future__ import annotations

import pytest

from frontier.interop.agent_card import (
    WELL_KNOWN_PATH,
    TaskState,
    agent_card_for_team,
    discovery,
)
from frontier.interop.deadlock import (
    leader_follower_handoff,
    supervisor_deadlock,
)


def test_mcp_round_trip_green_for_substantive_diff():
    pytest.importorskip("mcp")
    from frontier.interop.mcp_client import call_tool
    out = call_tool("run_tests", {"diff": "+ return xs[0] if xs else None"})
    assert out == "green"


def test_mcp_round_trip_red_for_junk_diff():
    pytest.importorskip("mcp")
    from frontier.interop.mcp_client import call_tool
    assert call_tool("run_tests", {"diff": "+ pass  # TODO"}) == "red"


def test_agent_card_has_required_spec_keys():
    card = agent_card_for_team().to_dict()
    for key in ("name", "url", "version", "protocolVersion",
                "capabilities", "skills"):
        assert key in card, key
    assert card["skills"], "the card must advertise at least one skill"
    ids = {s["id"] for s in card["skills"]}
    assert {"fix-failing-test", "review-diff", "run-tests"} <= ids


def test_discovery_returns_well_known_path():
    path, card = discovery(agent_card_for_team())
    assert path == WELL_KNOWN_PATH == "/.well-known/agent-card.json"
    assert card["name"] == "masact-coding-team"


def test_task_state_has_five_lifecycle_states():
    assert {s.name for s in TaskState} == {
        "SUBMITTED", "WORKING", "INPUT_REQUIRED", "COMPLETED", "FAILED"}


def test_supervisor_deadlock_valid_but_no_progress():
    result = supervisor_deadlock()
    assert result["all_schema_valid"] is True
    assert result["task_progressed"] is False
    assert result["diagnosis"] == "schemas green, task dead"
    assert result["messages"], "the exchange must actually exchange messages"
    # The deadlock never submits: no message carries the progress act.
    assert all(m["act"] != "submit" for m in result["messages"])


def test_leader_follower_handoff_is_the_positive_control():
    # Same message schema as the deadlock, but one side concedes the lead.
    # Progress must appear here --- proving the deadlock is the leadership
    # clash, not a rigged progress scan. Drive the two scenarios and compare.
    deadlock = supervisor_deadlock()
    handoff = leader_follower_handoff()
    # Both exchanges are equally schema-valid: form is not the difference.
    assert deadlock["all_schema_valid"] is True
    assert handoff["all_schema_valid"] is True
    # The only difference that matters is who agrees to be led.
    assert deadlock["task_progressed"] is False
    assert handoff["task_progressed"] is True
    assert handoff["diagnosis"] == "schemas green, task progressed"
    # Progress is real: a submit act is actually present in the handoff.
    assert any(m["act"] == "submit" for m in handoff["messages"])


def test_zero_rounds_is_not_vacuously_valid():
    # No messages exchanged must NOT report a green schema by vacuous truth.
    for scenario in (supervisor_deadlock, leader_follower_handoff):
        result = scenario(rounds=0)
        assert result["messages"] == []
        assert result["all_schema_valid"] is False
        assert result["task_progressed"] is False
