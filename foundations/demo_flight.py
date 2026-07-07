"""First flight, then the four crashes --- the §20.5 scenarios of Chapter 20.

Every run is deterministic (a ``FakeClient`` replaying a script, no tokens
spent), so the journals below are reproducible byte-for-byte. Run it with::

    python -m foundations.demo_flight

It prints two things the chapter quotes verbatim: the journal of the
successful first flight (the coder fails once, then passes), and one snippet
from each of the four deliberate crashes. The point the chapter makes is
visible in the raw: every outcome is a readable thread in a file we own.
"""

import json
import tempfile

from .budget import Budget
from .journal import events
from .mailbox import Mailbox
from .messages import Message, Performative
from .model import FakeClient, ModelResponse, ToolCall
from .team import Worker, run_team
from .tools import Tool


# --- terse builders, to keep the scripts under the 78-column cap ---------
def resp(usage, *calls, text=""):
    return ModelResponse(text=text, tool_calls=list(calls), usage=usage)


def call(name, **args):
    return ToolCall(name, args)


def done(**args):
    return ToolCall("done", args)


def worker(role, script, system, tools=()):
    return Worker(role, FakeClient(script), system, list(tools))


def scripted_runner(outcomes):
    """A test runner whose result changes call to call; an entry that is an
    Exception is raised (a flaky runner), so it comes back as an error
    observation rather than a result."""
    seq = iter(outcomes)

    def run_tests(**_):
        outcome = next(seq)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return Tool("run_tests", "Run the suite before claiming done.",
                {"name": "run_tests", "required": []}, run_tests)


def edit_tool():
    def edit_file(path, **_):
        return {"edited": path}
    return Tool("edit_file", "Edit a source file.",
                {"name": "edit_file", "required": ["path"]}, edit_file)


def render(evts, note="", drop=()):
    """The journal as the chapter shows it: one event per line, verbatim but
    for the schema-version ``v`` and timestamp ``t`` fields, which every line
    also carries and which are elided here for the page."""
    def trim(v):
        return v[:44] + "…" if isinstance(v, str) and len(v) > 46 else v

    lines = [f"# {note}"] if note else []
    for e in evts:
        if e["kind"] in drop:
            continue
        shown = {k: trim(v) for k, v in e.items() if k not in ("v", "t")}
        lines.append(json.dumps(shown, ensure_ascii=False))
    return "\n".join(lines)


def journal_path():
    return tempfile.mktemp(suffix=".jsonl")


def team(coder, reviewer, tester, task="Fix it."):
    jp = journal_path()
    outcome = run_team(task, coder, reviewer, tester,
                       journal_path=jp, budget=Budget(allowance=5000))
    return jp, outcome


# --- the successful first flight -----------------------------------------
def successful_flight():
    coder = worker("coder", [
        resp(120, call("run_tests"),
             text="Read the failing test; the empty-input guard is missing."),
        resp(95, call("run_tests"), text="Add the guard and re-run."),
        resp(60, done(summary="guard empty input",
                      diff="+ if not s: return []", tests="2 passed")),
    ], "You are the coder. Fix the failing test.",
        [scripted_runner([
            {"passed": 1, "failed": 1,
             "trace": "AssertionError: parse('') != []"},
            {"passed": 2, "failed": 0}])])
    reviewer = worker(
        "reviewer", [resp(40, done(verdict="accept"))],
        "You are the reviewer. Accept only sound changes.")
    tester = worker("tester", [
        resp(90, call("run_tests"), text="Run the full suite."),
        resp(30, done(verdict="green")),
    ], "You are the tester. Try to break the change.",
        [scripted_runner([{"passed": 2, "failed": 0}])])

    jp, _ = team(coder, reviewer, tester,
                 task="Make the failing parser test pass.")
    hdr = "journal.jsonl --- the successful first flight (abridged)"
    # abridged: drop the per-turn ModelCalled/BudgetDebited drumbeat
    return render(events(jp), note=hdr,
                  drop=("ModelCalled", "BudgetDebited"))


# --- crash 1: the vague subtask (duplicate work) -------------------------
def crash_vague_subtask():
    coder = worker("coder", [
        resp(80, call("edit_file", path="parser.py")),
        resp(40, done(diff="+ guard")),
    ], "Fix the bug.", [edit_tool()])
    reviewer = worker("reviewer", [resp(40, done(verdict="accept"))],
                      "Review.")
    tester = worker("tester", [   # the blurred boundary: the tester edits too
        resp(80, call("edit_file", path="parser.py")),
        resp(30, done(verdict="green")),
    ], "Verify.", [edit_tool()])
    jp, _ = team(coder, reviewer, tester, task="Fix it. (terse)")
    keep = [e for e in events(jp) if e.get("tool") == "edit_file"]
    note = ("crash 1 --- the vague subtask: the coder and the "
            "tester both edit the same file")
    return render(keep, note=note)


# --- crash 2: the silent dropout -----------------------------------------
def crash_silent_dropout():
    jp = journal_path()
    Mailbox(jp).send(Message(Performative.REQUEST, "orchestrator", "reviewer",
                             "T2", {"task": "review the diff"}))
    # the reviewer stub accepts the request and never replies; a collect step
    # without a deadline blocks here. The absence IS the trace.
    note = ("crash 2 --- the silent dropout: the request "
            "is delivered, no reply is ever appended")
    tail = ("\n# ...  (a naive collect blocks here; "
            "a deadline is the ~10-line fix)")
    return render(events(jp), note=note) + tail


# --- crash 3: the premature done -----------------------------------------
def crash_premature_done():
    coder = worker("coder", [resp(50, done(diff="+ x = y"))], "Fix the bug.")
    reviewer = worker(
        "reviewer",
        [resp(45, done(verdict="reject", reason="no test output"))],
        "Review.")
    tester = worker("tester", [resp(30, done(verdict="green"))], "Verify.")
    jp, outcome = team(coder, reviewer, tester)
    keep = [e for e in events(jp)
            if e["kind"] in ("MessageSent", "AgentFinished")]
    note = ("crash 3 --- the premature done: no ACCEPT, so integration "
            f"never runs (outcome: {outcome['status']})")
    return render(keep, note=note)


# --- crash 4: the tool error mid-turn ------------------------------------
def crash_tool_error():
    coder = worker("coder", [
        resp(70, call("run_tests")),   # dies
        resp(70, call("run_tests")),   # retried
        resp(40, done(diff="+ guard")),
    ], "Fix the bug.",
        [scripted_runner([RuntimeError("runner exited 137"),
                          {"passed": 2, "failed": 0}])])
    reviewer = worker("reviewer", [resp(40, done(verdict="accept"))],
                      "Review.")
    tester = worker("tester", [resp(30, done(verdict="green"))], "Verify.")
    jp, _ = team(coder, reviewer, tester)
    keep = [e for e in events(jp)
            if e.get("agent") == "coder" and e["kind"] == "ToolReturned"]
    note = ("crash 4 --- the tool error: the cryptic exit code "
            "returns as an observation, and loop policy retries")
    return render(keep, note=note)


def main():
    print("=" * 72)
    print(successful_flight())
    print("=" * 72)
    for scene in (crash_vague_subtask, crash_silent_dropout,
                  crash_premature_done, crash_tool_error):
        print(scene())
        print("-" * 72)


if __name__ == "__main__":
    main()
