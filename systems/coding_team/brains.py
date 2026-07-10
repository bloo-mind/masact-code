"""The model seam: a scripted brain for tests, an LLM brain for live runs.

The dependability machinery of the graph --- reducers, checkpoints, the human
gate, budgets, retries --- is entirely model-independent, so the graph takes a
``Brain`` and the tests inject a deterministic one. Swap in ``LLMBrain`` and
the same graph is driven by a real chat model. This is the ``Agent = Model +
Harness`` split of Chapter 3, drawn at the seam between the two.
"""

from __future__ import annotations

import os
from typing import Protocol

from .state import TeamState


class Brain(Protocol):
    """A role's decision-maker. Each method returns a small dict the matching
    graph node folds into the state; ``cost`` is charged to the treasury."""

    def code(self, state: TeamState) -> dict: ...
    def review(self, state: TeamState) -> dict: ...
    def test(self, state: TeamState) -> dict: ...


class ScriptedBrain:
    """Deterministic decisions --- no model, no tokens, no network.

    ``test_faults`` injects transient failures into the tester so the node's
    retry policy can be exercised; each raises once, then the call succeeds.
    """

    def __init__(self, *, verdict: str = "accept", suite: str = "green",
                 cost: int = 120, test_faults: int = 0):
        self.verdict = verdict
        self.suite = suite
        self.cost = cost
        self._faults = test_faults

    def code(self, state: TeamState) -> dict:
        return {"diff": ("+ words = text.split()\n"
                         "+ return words[0] if words else ''"),
                "note": "guard the empty-input case", "cost": self.cost}

    def review(self, state: TeamState) -> dict:
        return {"verdict": self.verdict, "reason": "checked the call sites",
                "cost": self.cost // 2}

    def test(self, state: TeamState) -> dict:
        if self._faults > 0:                 # a transient Heisenbug
            self._faults -= 1
            raise TimeoutError("test runner slow")
        return {"suite": self.suite, "cost": self.cost // 3}


class LLMBrain:
    """Live decisions from a chat model, via structured output.

    Reads the model name from ``MASACT_MODEL`` (default a mid-tier Claude
    model --- cheaper than the flagship, strong enough to ship the demo) and
    the key from the environment (``ANTHROPIC_API_KEY``); swap the model for
    any LangChain chat model to change provider. Token usage is read back from
    the response and charged to the treasury, so the budget is real.
    """

    def __init__(self, model: object | None = None):
        if model is None:
            from langchain_anthropic import ChatAnthropic
            name = os.environ.get("MASACT_MODEL", "claude-sonnet-5")
            # No temperature: omitted so the same call is valid on every tier
            # (the current Opus/Sonnet models reject sampling parameters), and
            # it never made sampling deterministic anyway.
            model = ChatAnthropic(model=name)
        self.model = model

    def _ask(self, schema: type, prompt: str) -> tuple[object, int]:
        bound = self.model.with_structured_output(schema, include_raw=True)
        out = bound.invoke(prompt)
        raw = out["raw"]
        usage = getattr(raw, "usage_metadata", None) or {}
        return out["parsed"], int(usage.get("total_tokens", 0))

    def code(self, state: TeamState) -> dict:
        from pydantic import BaseModel, Field

        class Change(BaseModel):
            diff: str = Field(
                description="a minimal patch, unified-diff style")
            note: str = Field(description="one line on what changed and why")

        prompt = _CODE_PROMPT.format(task=state["task"])
        if state.get("verdict") == "reject" and state.get("diff"):
            # A revision, not a re-roll: the coder sees what was rejected
            # and why, or the loop is three independent first attempts.
            reason = next((f for f in reversed(state["findings"])
                           if f.startswith("reviewer:")), "")
            prompt += _REVISE_SUFFIX.format(diff=state["diff"],
                                            reason=reason)
        parsed, cost = self._ask(Change, prompt)
        return {"diff": parsed.diff, "note": parsed.note, "cost": cost}

    def review(self, state: TeamState) -> dict:
        from pydantic import BaseModel, Field

        class Verdict(BaseModel):
            verdict: str = Field(description="'accept' or 'reject'")
            reason: str = Field(description="one line justifying the verdict")

        parsed, cost = self._ask(Verdict, _REVIEW_PROMPT.format(**state))
        # Fail closed: anything but the exact word "accept" is a rejection.
        v = parsed.verdict.strip().lower()
        verdict = v if v in ("accept", "reject") else "reject"
        return {"verdict": verdict, "reason": parsed.reason, "cost": cost}

    def test(self, state: TeamState) -> dict:
        from pydantic import BaseModel, Field

        class Result(BaseModel):
            suite: str = Field(description="'green' if it passes, else 'red'")

        parsed, cost = self._ask(Result, _TEST_PROMPT.format(**state))
        # Fail closed: anything but the exact word "green" is red.
        s = parsed.suite.strip().lower()
        suite = s if s in ("green", "red") else "red"
        return {"suite": suite, "cost": cost}


_CODE_PROMPT = (
    "You are the coder on a software-engineering team.\n"
    "Task: {task}\n"
    "Propose the smallest change that resolves it."
)
_REVISE_SUFFIX = (
    "\nYour previous patch was rejected in review.\n"
    "Rejected patch:\n{diff}\n"
    "Review finding: {reason}\n"
    "Address the finding; do not resubmit the same patch."
)
_REVIEW_PROMPT = (
    "You are the reviewer. The coder proposed this change for the task "
    "'{task}':\n{diff}\nAccept it only if it is correct and minimal."
)
_TEST_PROMPT = (
    "You are the tester. The integrated change for '{task}' is:\n{diff}\n"
    "Report whether the suite is green or red."
)
