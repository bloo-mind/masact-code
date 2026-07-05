"""The triple experiment (Chapter 24): team vs strong single agent vs
workflow.

The honest question is never "is the team good?" but "is it better than the
strongest thing I would otherwise build, and at what cost?" This harness runs
several systems on the *same* tasks, judges each output, and reports the
paired comparison --- reusing the tested ``paired_t`` from the foundations
layer, so the statistics are the same in the lab as on the page.
"""

from __future__ import annotations

from collections.abc import Callable

from foundations.algorithms.evaluation import paired_t

Runner = Callable[[str], str]          # task -> output artefact
Judge = Callable[[str, str], float]    # (task, output) -> quality in [0, 1]


def run_suite(runner: Runner, tasks: list[str], judge: Judge) -> list[float]:
    """Score one system on the task set: one quality per task."""
    return [judge(task, runner(task)) for task in tasks]


def compare(scores: dict[str, list[float]]) -> dict:
    """Mean quality per system over the same tasks, and --- for exactly two
    systems --- the paired t, task difficulty cancelled by the pairing."""
    means = {name: sum(v) / len(v) for name, v in scores.items()}
    result: dict = {"means": means}
    if len(scores) == 2:
        (name_a, sa), (name_b, sb) = scores.items()
        result["paired"] = {"a": name_a, "b": name_b, **paired_t(sa, sb)}
    return result


def team_runner(brain: object) -> Runner:
    """The full team: coder, reviewer, gate, tester. Returns the shipped diff
    (empty if the change never merged)."""
    from systems.coding_team import build_team, run_team

    app = build_team(brain)

    def run(task: str) -> str:
        final = run_team(app, task, thread_id=f"eval-{hash(task) & 0xffff}")
        return final["diff"] if final["status"] == "shipped" else ""

    return run


def single_agent_runner(brain: object) -> Runner:
    """The strong single agent: one coder pass, no review or test --- the
    baseline the team must beat to justify its coordination cost."""
    from systems.coding_team import initial_state

    def run(task: str) -> str:
        return brain.code(initial_state(task))["diff"]

    return run


def workflow_runner(patch: str = "+ # fixed-pipeline change") -> Runner:
    """A fixed deterministic workflow: cheap, testable, and often enough."""
    def run(task: str) -> str:
        return patch

    return run
