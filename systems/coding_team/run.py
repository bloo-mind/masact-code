"""Run the hardened team.

    uv run python -m systems.coding_team.run             # scripted, no key
    uv run python -m systems.coding_team.run --live      # real model

``--live`` loads a git-ignored ``.env`` (copy ``.env.example``) for
``OPENAI_API_KEY`` and uses ``MASACT_MODEL`` (default ``gpt-4o-mini``).
"""

from __future__ import annotations

import sys

from .brains import LLMBrain, ScriptedBrain
from .graph import build_team, run_team


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    live = "--live" in argv

    if live:
        from dotenv import load_dotenv
        load_dotenv()                        # OPENAI_API_KEY from .env
        brain = LLMBrain()
        print("running the team on a live model...")
    else:
        brain = ScriptedBrain()
        print("running the team on a scripted brain (no key, deterministic)...")

    app = build_team(brain)
    final = run_team(app, "Make the failing parser test pass.")
    print(f"status: {final['status']} | suite: {final['suite']} "
          f"| spent: {final['spent']} tokens")
    for f in final["findings"]:
        print("  -", f)


if __name__ == "__main__":
    main()
