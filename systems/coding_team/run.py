"""Run the hardened team.

    uv run python -m systems.coding_team.run             # scripted, no key
    uv run python -m systems.coding_team.run --live      # real model

``--live`` loads a git-ignored ``.env`` (copy ``.env.example``) for
``ANTHROPIC_API_KEY`` and uses ``MASACT_MODEL`` (default ``claude-sonnet-5``).
"""

from __future__ import annotations

import sys

from .brains import LLMBrain, ScriptedBrain
from .graph import build_team, run_team

# A self-contained task: the bug and the failing test that pins it are on the
# page, so the coder can propose a real fix and the reviewer can check it
# against the test --- a capable model ships rather than guessing blind.
_TASK = (
    "This helper should return the first whitespace-separated word of a "
    "string, or an empty string when the input is blank:\n\n"
    "    def first_word(text):\n"
    "        return text.split()[0]\n\n"
    "It fails the test `assert first_word('   ') == ''` --- split() returns "
    "an empty list, so [0] raises IndexError. Propose the smallest fix."
)


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    live = "--live" in argv

    if live:
        from dotenv import load_dotenv
        load_dotenv()                        # ANTHROPIC_API_KEY from .env
        brain = LLMBrain()
        print("running the team on a live model...")
    else:
        brain = ScriptedBrain()
        print(
            "running the team on a scripted brain (no key, deterministic)...")

    app = build_team(brain)
    final = run_team(app, _TASK)   # the merge gate is auto-approved here
    print("(the human merge gate is auto-approved so the demo is "
          "non-interactive; a deployment parks there)")
    print(f"status: {final['status']} | suite: {final['suite']} "
          f"| spent: {final['spent']} tokens")
    for f in final["findings"]:
        print("  -", f)
    if final["suite"]:
        print("note: the tester's verdict is a model's reading of the diff, "
              "not an executed suite --- Chapter 24 builds the executable "
              "oracle.")


if __name__ == "__main__":
    main()
