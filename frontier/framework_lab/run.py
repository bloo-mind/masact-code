"""CLI for the Chapter 19 framework lab: one job across framework positions.

    python -m frontier.framework_lab.run          # hermetic (scripted)
    python -m frontier.framework_lab.run --live    # one shared Claude model

Default mode compares the LangGraph team against the plain single-agent
baseline with scripted brains --- no key, no network. ``--live`` swaps in a
single shared Claude model (systems ``LLMBrain``) under both positions, and
adds the Claude Agent SDK runner when the ``claude`` CLI is on ``PATH``:
every position runs the same model, so the scorecard measures the framework,
not the model. It prints the four-column scorecard and the failure-behaviour
table --- the column that repays the exercise.
"""

from __future__ import annotations

import argparse
import os
import shutil

from ..rig import Runner
from ..runners import claude_agent_runner, langgraph_runner, plain_runner
from ..tasks import coupled_task
from .scorecard import Fault, failure_behaviour_table, scorecard


def _build_runners(live: bool) -> dict[str, Runner]:
    """The framework positions to score, all over one held-fixed model."""
    from systems.coding_team import LLMBrain, ScriptedBrain

    if not live:
        return {
            "langgraph": langgraph_runner(ScriptedBrain()),
            "plain": plain_runner(ScriptedBrain()),
        }

    from dotenv import load_dotenv
    load_dotenv()                         # ANTHROPIC_API_KEY from a .env
    brain = LLMBrain()                    # one model under every position
    runners: dict[str, Runner] = {
        "langgraph": langgraph_runner(brain),
        "plain": plain_runner(brain),
    }
    if shutil.which("claude"):
        # Same-model control: the vendor SDK must run the SHARED model, not
        # its own hardcoded default, or its scorecard row measures the model.
        model = os.environ.get("MASACT_MODEL", "claude-sonnet-5")
        runners["claude_agent_sdk"] = claude_agent_runner(model=model)
    return runners


def _print_scorecard(board: dict[str, dict[str, float]]) -> None:
    head = (f"{'framework':<18}{'quality':>9}{'tokens':>9}"
            f"{'latency_s':>11}{'failures':>10}{'loc':>6}")
    print(head)
    for name, c in board.items():
        print(f"{name:<18}{c['quality']:>9.2f}{c['tokens']:>9.0f}"
              f"{c['latency_s']:>11.4f}{c['failures']:>10.0f}"
              f"{c['loc']:>6.0f}")


def _print_table(table: dict[str, dict[str, str]],
                 faults: list[Fault]) -> None:
    cols = [f.name for f in faults]
    print(f"{'framework':<18}" + "".join(f"{c:>18}" for c in cols))
    for name, row in table.items():
        print(f"{name:<18}" + "".join(f"{row[c]:>18}" for c in cols))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Chapter 19 framework scorecard.")
    parser.add_argument(
        "--live", action="store_true",
        help="run one shared Claude model under each framework position")
    args = parser.parse_args(argv)

    task = coupled_task().prompt
    runners = _build_runners(args.live)
    faults = [Fault.TOOL_ERROR, Fault.TIMEOUT, Fault.MALFORMED]

    print("Four-column scorecard (same model underneath):")
    _print_scorecard(scorecard(runners, task))
    print("\nFailure-behaviour table (the real separator):")
    _print_table(failure_behaviour_table(runners, faults), faults)


if __name__ == "__main__":
    main()
