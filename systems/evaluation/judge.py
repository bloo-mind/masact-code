"""LLM-as-judge and its calibration (Chapter 24).

A judge is a callable ``(task, output) -> quality in [0, 1]``. The scripted judge
is deterministic (for tests); the LLM judge rubric-scores with a real model. A
judge is an instrument, so it is calibrated against human labels --- and the
``agreement`` helper reports how often it and the humans reach the same verdict.
"""

from __future__ import annotations

import os
from statistics import mean


class ScriptedJudge:
    """Deterministic quality --- a lookup or a rule; no model."""

    def __init__(self, quality: object):
        self.quality = quality          # dict[(task, output) -> q] or callable

    def __call__(self, task: str, output: str) -> float:
        if callable(self.quality):
            return float(self.quality(task, output))
        return float(self.quality.get((task, output),
                                      1.0 if output else 0.0))


class LLMJudge:
    """Rubric scoring from a real chat model (0 = useless, 1 = resolves it)."""

    def __init__(self, model: object | None = None):
        if model is None:
            from langchain_openai import ChatOpenAI
            name = os.environ.get("MASACT_MODEL", "gpt-4o-mini")
            model = ChatOpenAI(model=name, temperature=0)
        self.model = model

    def __call__(self, task: str, output: str) -> float:
        from pydantic import BaseModel, Field

        class Score(BaseModel):
            quality: float = Field(ge=0.0, le=1.0,
                                   description="how well the output resolves "
                                               "the task, 0 to 1")

        prompt = (f"Task: {task}\nProposed output:\n{output}\n"
                  f"Score how well it resolves the task, from 0 to 1.")
        return float(self.model.with_structured_output(Score)
                     .invoke(prompt).quality)


def agreement(judge_scores: list[float], human_scores: list[float],
              threshold: float = 0.5) -> float:
    """Fraction of items on which judge and humans agree pass/fail --- the
    calibration number a judge's grades are only as trustworthy as."""
    return mean(1.0 if (j >= threshold) == (h >= threshold) else 0.0
                for j, h in zip(judge_scores, human_scores))
