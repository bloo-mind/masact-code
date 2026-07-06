"""CLI for the interoperability lab (Chapter 22): a tour of three altitudes.

Publish the team's Agent Card at its well-known path, round-trip an MCP
``run_tests`` call in-memory (green on a real diff, red on junk), and run the
supervisor-meets-supervisor deadlock demo. No key, no network --- the MCP
round-trip uses the in-memory transport.
"""

from __future__ import annotations

import json

from .agent_card import agent_card_for_team, discovery
from .deadlock import leader_follower_handoff, supervisor_deadlock
from .mcp_client import call_tool


def main() -> None:
    # --- Agent altitude: publish the card at the well-known path ----------
    path, card = discovery(agent_card_for_team())
    print(f"# Agent Card published at {path}")
    print(json.dumps(card, indent=2))

    # --- Tool altitude: round-trip an MCP run_tests call in-memory --------
    real_diff = "+ return xs[0] if xs else None"
    junk_diff = "+ pass  # TODO"
    print("\n# MCP run_tests round-trip (in-memory)")
    print(f"  real diff -> {call_tool('run_tests', {'diff': real_diff})}")
    print(f"  junk diff -> {call_tool('run_tests', {'diff': junk_diff})}")

    # --- Interop failure: two supervisors, both awaiting the other --------
    result = supervisor_deadlock()
    print("\n# Supervisor-meets-supervisor deadlock")
    print(f"  messages exchanged: {len(result['messages'])}")
    print(f"  all schema-valid:   {result['all_schema_valid']}")
    print(f"  task progressed:    {result['task_progressed']}")
    print(f"  {result['diagnosis']}")

    # --- Positive control: same schema, but one side concedes the lead ----
    control = leader_follower_handoff()
    print("\n# Positive control: leader meets follower")
    print(f"  messages exchanged: {len(control['messages'])}")
    print(f"  all schema-valid:   {control['all_schema_valid']}")
    print(f"  task progressed:    {control['task_progressed']}")
    print(f"  {control['diagnosis']}")


if __name__ == "__main__":
    main()
