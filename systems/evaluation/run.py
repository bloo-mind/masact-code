"""Run the triple experiment: team vs strong single agent vs fixed workflow.

    uv run python -m systems.evaluation.run           # scripted, no key
    uv run python -m systems.evaluation.run --live    # real model + LLM judge

``--live`` loads a git-ignored ``.env`` (copy ``.env.example``) for
``ANTHROPIC_API_KEY`` and uses ``MASACT_MODEL`` (default ``claude-opus-4-8``).
"""

from __future__ import annotations

import sys

from .harness import (
    compare, run_suite, single_agent_runner, team_runner, workflow_runner,
)
from .judge import LLMJudge, ScriptedJudge

_TASKS = [
    "make the failing parser test pass",
    "guard the list index against an empty input",
    "handle the empty-collection edge case",
]


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    live = "--live" in argv

    if live:
        from dotenv import load_dotenv

        from systems.coding_team import LLMBrain
        load_dotenv()                        # ANTHROPIC_API_KEY from .env
        brain: object = LLMBrain()
        judge: object = LLMJudge()
        print("running the triple experiment on a live model...")
    else:
        from systems.coding_team import ScriptedBrain
        brain = ScriptedBrain()
        judge = ScriptedJudge(lambda t, out: 1.0 if "return" in out else 0.4)
        print("running the triple experiment on a scripted brain (no key)...")

    scores = {
        "team": run_suite(team_runner(brain), _TASKS, judge),
        "single": run_suite(single_agent_runner(brain), _TASKS, judge),
        "workflow": run_suite(workflow_runner(), _TASKS, judge),
    }
    for name in ("team", "single", "workflow"):
        mean_q = sum(scores[name]) / len(scores[name])
        print(f"  {name:8s} mean quality: {mean_q:.3f}")

    # the headline question: is the team better than a strong single agent?
    result = compare({"team": scores["team"], "single": scores["single"]})
    paired = result["paired"]
    print(f"  team vs single: mean_d {paired['mean_d']:+.3f}, "
          f"t {paired['t']:.2f} on {len(_TASKS) - 1} d.f.")
    if paired["t"] == 0.0:
        print("  (a scripted brain makes the two textually identical, so the "
              "paired test correctly reports no signal --- run --live to "
              "distinguish them)")


if __name__ == "__main__":
    main()
