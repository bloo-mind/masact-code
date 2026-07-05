"""First flight: the software-engineering team resolves a toy task end to end.

Run it with::

    python -m foundations.demo_team

Every model here is a ``FakeClient`` replaying a script, so the demo is
deterministic and spends no tokens. Swap in a real ``ModelClient`` --- one
that calls an actual provider --- and the same harness drives a live team.
The whole run is a single journal file, folded and printed at the end.
"""

import tempfile

from .budget import Budget
from .journal import events, fold
from .model import FakeClient, ModelResponse, ToolCall
from .team import Worker, run_team
from .tools import Tool


def _run_tests(**_: object) -> dict:
    # A real runner would shell out; here the suite is green by fiat.
    return {"passed": 2, "failed": 0}


def build_team() -> tuple[Worker, Worker, Worker]:
    run_tests = Tool("run_tests", "Run the suite before claiming done.",
                     {"name": "run_tests", "required": []}, _run_tests)

    # The coder checks the suite, then signals done with its diff.
    coder = Worker("coder", FakeClient([
        ModelResponse(text="Let me run the suite.",
                      tool_calls=[ToolCall("run_tests", {})], usage=120),
        ModelResponse(tool_calls=[ToolCall(
            "done", {"summary": "guard empty input", "diff": "+ if not x:"})],
            usage=60),
    ]), "You are the coder. Fix the failing test.", [run_tests])

    # The reviewer reads the diff and votes accept.
    reviewer = Worker("reviewer", FakeClient([
        ModelResponse(tool_calls=[ToolCall(
            "done", {"verdict": "accept"})], usage=40),
    ]), "You are the reviewer. Accept only sound changes.")

    # The tester runs the integrated result and reports green.
    tester = Worker("tester", FakeClient([
        ModelResponse(text="Running the full suite.",
                      tool_calls=[ToolCall("run_tests", {})], usage=90),
        ModelResponse(tool_calls=[ToolCall(
            "done", {"verdict": "green"})], usage=30),
    ]), "You are the tester. Try to break the change.", [run_tests])

    return coder, reviewer, tester


def main() -> None:
    journal = tempfile.mktemp(suffix=".jsonl")
    coder, reviewer, tester = build_team()
    outcome = run_team("Make the failing parser test pass.",
                       coder, reviewer, tester,
                       journal_path=journal, budget=Budget(allowance=5000))
    print("outcome:", outcome["status"], "| suite:", outcome.get("suite"))
    print("journal (folded):", fold(events(journal)))
    print(f"{len(events(journal))} events at {journal}")


if __name__ == "__main__":
    main()
