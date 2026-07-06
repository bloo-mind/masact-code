"""Runners: ``task -> RunResult``, scripted for tests, live for the frontier.

The instruments (scorecards, sweeps, censuses) are model-independent; the
runners are the dated seam where a real framework or vendor SDK plugs in. A
scripted runner makes the whole layer testable with no key and no network;
the live runners reuse the tested Chapter 23 team and a single-agent
baseline, plus dated Claude Agent SDK and CrewAI adapters --- the graph
runtime, the vendor agent SDK, and the declarative crew of Chapter 19.

Same-model control (Chapter 19's insistence) is the caller's job: pass one
``brain`` / ``model`` to every runner being compared, or the comparison
measures the model, not the framework.
"""

from __future__ import annotations

from collections.abc import Callable

from .rig import (
    AGENT_FINISHED, MESSAGE_SENT, REVIEWED, RUN_STARTED, TESTED, RunResult,
    Runner, run_timed,
)

Judge = Callable[[str, str], float]   # (task, output) -> quality in [0, 1]


def _default_quality(output: str) -> float:
    """A judge-free fallback: a substantive diff scores 1, empty scores 0."""
    return 1.0 if output and "return" in output else (0.4 if output else 0.0)


# --- Scripted: deterministic, no model, no network (for tests) ------------

def scripted_runner(*, output: str = "+ return xs[0] if xs else None",
                    quality: float | None = None, tokens: int = 200,
                    status: str = "shipped",
                    failures: list[str] | None = None) -> Runner:
    """A deterministic runner --- no model --- for hermetic tests."""
    def run(task: str) -> RunResult:
        q = quality if quality is not None else _default_quality(output)
        r = RunResult(task=task, output=output, status=status, quality=q,
                      tokens=tokens, failures=list(failures or []))
        r.log(RUN_STARTED, task[:40])
        r.log(AGENT_FINISHED, status)
        return r
    return run


# --- LangGraph team: the Chapter 23 build (a graph runtime) ---------------

def langgraph_runner(brain: object | None = None,
                     judge: Judge | None = None) -> Runner:
    """The Chapter 23 LangGraph team as a measured runner. The findings are
    mapped into the journal so the pattern detectors can read them."""
    from systems.coding_team import ScriptedBrain, build_team, run_team
    app = build_team(brain if brain is not None else ScriptedBrain())

    def run(task: str) -> RunResult:
        def _go() -> RunResult:
            final = run_team(app, task, thread_id=f"fl-{hash(task) & 0xffff}")
            out = final["diff"] if final["status"] == "shipped" else ""
            q = (judge(task, out) if judge is not None
                 else (1.0 if final["status"] == "shipped" else 0.0))
            r = RunResult(task=task, output=out, status=final["status"],
                          quality=q, tokens=final["spent"])
            r.log(RUN_STARTED, task[:40])
            for finding in final["findings"]:
                if finding.startswith("reviewer:"):
                    r.log(REVIEWED, finding)
                elif finding.startswith("tester:"):
                    r.log(TESTED, final["suite"])
                else:
                    r.log(MESSAGE_SENT, finding)
            r.log(AGENT_FINISHED, final["status"])
            return r
        return run_timed(_go)
    return run


# --- Plain single agent: no framework (the standing baseline) -------------

def plain_runner(brain: object | None = None,
                 judge: Judge | None = None) -> Runner:
    """One agent, one pass, no review or test loop --- the framework-free
    baseline Chapters 19 and 27 insist a team must beat to earn its keep."""
    from systems.coding_team import LLMBrain, initial_state
    b = brain if brain is not None else LLMBrain()

    def run(task: str) -> RunResult:
        def _go() -> RunResult:
            change = b.code(initial_state(task))
            out = change["diff"]
            q = (judge(task, out) if judge is not None
                 else _default_quality(out))
            r = RunResult(task=task, output=out,
                          status="shipped" if out else "failed", quality=q,
                          tokens=change["cost"])
            r.log(RUN_STARTED, task[:40])
            r.log(MESSAGE_SENT, f"coder: {change.get('note', '')}")
            r.log(AGENT_FINISHED, r.status)
            return r
        return run_timed(_go)
    return run


# --- Claude Agent SDK: a vendor agent SDK (dated; needs the `claude` CLI) --

_AGENT_SYSTEM = (
    "You are a coder. Given a bug and its failing test, reply with the "
    "smallest unified-diff patch that makes the test pass. Diff only.")


def claude_agent_runner(model: str = "claude-sonnet-5",
                        judge: Judge | None = None) -> Runner:
    """The Claude Agent SDK as a runner (a vendor agent SDK type specimen).

    Dated: ``claude-agent-sdk`` drives the ``claude`` CLI as its agent
    runtime, so this needs that binary on ``PATH`` and ``ANTHROPIC_API_KEY``.
    The hermetic tests skip it; it is here for the live framework comparison.
    """
    def run(task: str) -> RunResult:
        def _go() -> RunResult:
            import asyncio

            from claude_agent_sdk import (
                ClaudeAgentOptions, ResultMessage, query,
            )

            async def _collect() -> tuple[str, int]:
                # Two isolations make this a code-completer rather than a
                # crash: no tools (the bug is self-contained --- no workspace
                # to Read/Edit), and ``setting_sources=[]`` so the spawned
                # ``claude`` CLI ignores the host's own settings, hooks, and
                # plugins, whose events otherwise flood the turn budget.
                opts = ClaudeAgentOptions(system_prompt=_AGENT_SYSTEM,
                                          model=model, allowed_tools=[],
                                          setting_sources=[], max_turns=3)
                out, tokens = "", 0
                async for msg in query(prompt=task, options=opts):
                    if isinstance(msg, ResultMessage):
                        out = msg.result or ""
                        usage = msg.usage or {}
                        get = (usage.get if isinstance(usage, dict)
                               else lambda k, d=0: getattr(usage, k, d))
                        tokens = int(get("input_tokens", 0)
                                     + get("output_tokens", 0))
                return out, tokens

            out, tokens = asyncio.run(_collect())
            q = (judge(task, out) if judge is not None
                 else _default_quality(out))
            r = RunResult(task=task, output=out,
                          status="shipped" if out else "failed", quality=q,
                          tokens=tokens)
            r.log(RUN_STARTED, task[:40])
            r.log(AGENT_FINISHED, r.status)
            return r
        return run_timed(_go)
    return run


# --- CrewAI: a declarative crew (dated; a heavy vendor framework) ---------

def crew_runner(model: str = "claude-sonnet-5",
                judge: Judge | None = None) -> Runner:
    """A declarative crew (CrewAI) as a runner --- Chapter 19's third
    framework position. The agent and its task are *declared*; the framework
    owns the loop. Dated and heavy; needs a provider key, and runs the shared
    model through litellm's ``anthropic/<model>`` for same-model control. This
    is where the lines-of-code column wins most dramatically --- and, the book
    warns, most misleadingly, since the win measures the decisions you did not
    get to make."""
    def run(task: str) -> RunResult:
        def _go() -> RunResult:
            import os
            os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
            os.environ.setdefault("OTEL_SDK_DISABLED", "true")

            from crewai import LLM, Agent, Crew, Task

            coder = Agent(
                role="Coder",
                goal="Fix the bug with the smallest possible patch",
                backstory="You reply with a unified diff and nothing else.",
                llm=LLM(model=f"anthropic/{model}"), verbose=False)
            job = Task(description=task,
                       expected_output="a minimal unified-diff patch",
                       agent=coder)
            out = Crew(agents=[coder], tasks=[job], verbose=False).kickoff()
            text = str(out.raw or "")
            usage = out.token_usage
            tokens = int(getattr(usage, "total_tokens", 0) or 0)
            q = (judge(task, text) if judge is not None
                 else _default_quality(text))
            r = RunResult(task=task, output=text,
                          status="shipped" if text else "failed", quality=q,
                          tokens=tokens)
            r.log(RUN_STARTED, task[:40])
            r.log(AGENT_FINISHED, r.status)
            return r
        return run_timed(_go)
    return run
