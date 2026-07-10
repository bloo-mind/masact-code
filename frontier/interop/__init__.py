"""The interoperability lab (Chapter 22): three altitudes of interop.

Chapter 22 stacks interoperability at three altitudes --- the *model*
(shared weights and formats), the *tool* (the Model Context Protocol, MCP),
and the *agent* (agent-to-agent discovery, A2A) --- and then closes on the
failure that no protocol can fix: two supervisors, each schema-valid, each
polite, deadlocked over who leads (Section 22.5).

This package is one instrument per altitude, over the shared frontier rig:

* :mod:`frontier.interop.mcp_server` --- one team tool wrapped as a real MCP
  server (the tool altitude).
* :mod:`frontier.interop.mcp_client` --- call that tool, in-memory (hermetic)
  or over stdio (the real cross-process path).
* :mod:`frontier.interop.agent_card` --- the A2A Agent Card, an advertisement
  a team publishes at a well-known address (the agent altitude).
* :mod:`frontier.interop.deadlock` --- supervisor-meets-supervisor: every
  message valid, no progress (the interop-failure lab).
"""

from __future__ import annotations

from .agent_card import (
    WELL_KNOWN_PATH,
    AgentCard,
    AgentSkill,
    TaskState,
    agent_card_for_team,
    discovery,
)
from .deadlock import leader_follower_handoff, supervisor_deadlock

try:  # the tool altitude needs the optional ``mcp`` extra; the agent
    from .mcp_client import call_tool, call_tool_stdio
    from .mcp_server import build_server
except ImportError:  # altitude and the deadlock lab work without it
    call_tool = call_tool_stdio = build_server = None  # type: ignore[assignment]

__all__ = [
    "build_server",
    "call_tool",
    "call_tool_stdio",
    "WELL_KNOWN_PATH",
    "AgentCard",
    "AgentSkill",
    "TaskState",
    "agent_card_for_team",
    "discovery",
    "supervisor_deadlock",
    "leader_follower_handoff",
]
