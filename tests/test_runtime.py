"""Tests for the Chapter 20 runtime."""

import tempfile

from foundations import (
    Budget, FakeClient, Mailbox, Message, ModelResponse, Performative,
    Tool, ToolCall, Worker, append, assemble, dispatch, events, fold,
    integrate, run, run_team,
)
from foundations.demo_team import build_team


def _journal() -> str:
    return tempfile.mktemp(suffix=".jsonl")


def _run_tests(**_):
    return {"test_api": "pass"}


def _tool():
    return Tool("run_tests", "run the suite",
                {"name": "run_tests", "required": []}, _run_tests)


def test_dispatch_happy_path():
    assert dispatch(_tool(), {}) == {"tool": "run_tests",
                                     "result": {"test_api": "pass"}}


def test_dispatch_missing_argument_is_an_observation():
    t = Tool("edit", "edit a file",
             {"name": "edit", "required": ["path"]}, lambda path: path)
    assert dispatch(t, {}) == {"tool": "edit",
                               "error": "missing argument: path"}


def test_dispatch_exception_is_an_observation():
    def boom():
        raise RuntimeError("disk on fire")
    obs = dispatch(Tool("boom", "explodes", {"required": []}, boom), {})
    assert obs["error"] == "RuntimeError: disk on fire"


def test_assemble_keeps_ends_and_compacts_the_middle():
    history = [f"step {i} " + "x" * 50 for i in range(40)]
    ctx = assemble("sys", "task", history, ["fresh observation"], limit=800)
    assert ctx[0] == {"role": "system", "content": "sys"}
    assert ctx[1] == {"role": "user", "content": "task"}
    assert "compacted" in ctx[2]["content"]
    assert ctx[-1] == {"role": "user", "content": "fresh observation"}


def test_loop_runs_tool_then_finishes():
    script = [
        ModelResponse(text="checking",
                      tool_calls=[ToolCall("run_tests", {})], usage=100),
        ModelResponse(tool_calls=[ToolCall("done", {"summary": "ok"})],
                      usage=50),
    ]
    j, budget = _journal(), Budget(1000)
    result = run("coder", FakeClient(script), [_tool()], "sys", "task",
                 j, budget)
    assert result == {"status": "done", "summary": "ok"}
    assert budget.spent == 150
    assert fold(events(j)) == {"spent": 150, "finished": ["coder"],
                               "messages": 0}


def test_loop_winds_down_when_budget_exhausted():
    script = [ModelResponse(text="thinking", usage=900),
              ModelResponse(text="still thinking", usage=900)]
    result = run("dreamer", FakeClient(script), [], "sys", "task",
                 _journal(), Budget(1000))
    assert result["status"] == "halted"


def test_loop_stops_after_two_consecutive_drifts():
    script = [ModelResponse(text="musing", usage=10),
              ModelResponse(text="musing on", usage=10)]
    result = run("waffler", FakeClient(script), [], "sys", "task",
                 _journal(), Budget(10_000))
    assert result["status"] == "inconclusive"


def test_journal_survives_a_reread():
    j = _journal()
    append(j, "RunStarted", agent="a", task="t")
    append(j, "BudgetDebited", agent="a", amount=42)
    # Fold, throw the view away, fold again: state is recomputed, not stored.
    assert fold(events(j)) == fold(events(j))
    assert fold(events(j))["spent"] == 42


def test_mailbox_journals_send_and_delivery():
    j = _journal()
    box = Mailbox(j)
    box.send(Message(Performative.DONE, "coder", "orch", "T1", {"x": 1}))
    assert [m.payload for m in box.drain("orch")] == [{"x": 1}]
    kinds = [e["kind"] for e in events(j)]
    assert kinds == ["MessageSent", "MessageDelivered"]


def test_integrate_refuses_without_accept():
    j = _journal()
    box = Mailbox(j)
    box.send(Message(Performative.DONE, "coder", "orch", "T1", {}))
    inbox = box.drain("orch")
    try:
        integrate(inbox, "T1", lambda: "merged")
        assert False, "gate should have refused"
    except PermissionError:
        pass


def test_integrate_admits_on_accept():
    j = _journal()
    box = Mailbox(j)
    box.send(Message(Performative.ACCEPT, "reviewer", "orch", "T1", {}))
    assert integrate(box.drain("orch"), "T1", lambda: "merged") == "merged"


def test_run_team_ships_on_accept():
    coder, reviewer, tester = build_team()
    outcome = run_team("fix the parser", coder, reviewer, tester,
                       _journal(), Budget(5000))
    assert outcome["status"] == "shipped"
    assert outcome["suite"] == "green"


def test_run_team_rejects_without_reviewer_accept():
    coder, _, tester = build_team()
    naysayer = Worker("reviewer", FakeClient([
        ModelResponse(tool_calls=[ToolCall("done", {"verdict": "reject"})],
                      usage=40)]), "You reject everything.")
    outcome = run_team("fix the parser", coder, naysayer, tester,
                       _journal(), Budget(5000))
    assert outcome["status"] == "rejected"


class _Advertised(FakeClient):
    """A FakeClient that records the tool schemas it was shown."""

    def __init__(self, script):
        super().__init__(script)
        self.shown: list[list[dict]] = []

    def complete(self, messages, tools):
        self.shown.append(tools)
        return super().complete(messages, tools)


def test_loop_advertises_the_done_tool():
    # A real tool-calling model can only call what is declared to it, so
    # the loop's own verb must be on offer alongside the caller's tools.
    client = _Advertised([
        ModelResponse(tool_calls=[ToolCall("done", {})], usage=10)])
    run("finisher", client, [_tool()], "sys", "task",
        _journal(), Budget(100))
    names = [s.get("name") for s in client.shown[0]]
    assert "run_tests" in names and "done" in names


def test_loop_turns_unknown_tool_into_an_observation():
    # A hallucinated tool name is an error observation, not a crash.
    script = [
        ModelResponse(tool_calls=[ToolCall("imaginary", {})], usage=10),
        ModelResponse(tool_calls=[ToolCall("done", {"note": "ok"})],
                      usage=10),
    ]
    j = _journal()
    result = run("dreamer", FakeClient(script), [_tool()], "sys", "task",
                 j, Budget(1000))
    assert result["status"] == "done"
    returned = [e for e in events(j) if e["kind"] == "ToolReturned"]
    assert returned and returned[0]["error"] == "unknown tool"


def test_done_cannot_forge_the_harness_status():
    # The harness owns the verdict: a done(status=...) payload must not
    # overwrite it.
    script = [ModelResponse(
        tool_calls=[ToolCall("done", {"status": "forged", "note": "x"})],
        usage=10)]
    result = run("forger", FakeClient(script), [], "sys", "task",
                 _journal(), Budget(100))
    assert result["status"] == "done"
    assert result["note"] == "x"


def test_events_tolerates_a_torn_final_line():
    # A crash mid-append leaves a torn last line; the reader returns the
    # intact prefix rather than raising at the worst possible moment.
    j = _journal()
    append(j, "RunStarted", agent="a", task="t")
    append(j, "BudgetDebited", agent="a", amount=7)
    with open(j, "a") as f:
        f.write('{"v": 1, "t": 0, "kind": "Model')   # died mid-write
    evts = events(j)
    assert [e["kind"] for e in evts] == ["RunStarted", "BudgetDebited"]
    assert fold(evts)["spent"] == 7
