"""Hermetic tests for the Chapter 24 evaluation harness.

The statistics (``run_suite``, ``compare``, ``agreement``) need no model and no
framework, so they run in the core suite. The triple-experiment integration
drives the real LangGraph team through a scripted brain, so it skips when the
systems extra is absent.
"""

import pytest

from foundations.algorithms.evaluation import paired_t
from systems.evaluation import (
    ScriptedJudge, agreement, compare, run_suite, single_agent_runner,
    team_runner, workflow_runner,
)


def test_run_suite_scores_each_task():
    runner = lambda task: task.upper()               # noqa: E731
    judge = ScriptedJudge(lambda task, out: len(out) / 10.0)
    scores = run_suite(runner, ["ab", "abcd"], judge)
    assert scores == [0.2, 0.4]


def test_scripted_judge_lookup_and_default():
    judge = ScriptedJudge({("t", "good"): 0.9})
    assert judge("t", "good") == 0.9                 # looked up
    assert judge("t", "unseen") == 1.0               # non-empty default
    assert judge("t", "") == 0.0                     # empty output


def test_compare_paired_matches_foundations():
    a = [0.82, 0.77, 0.91, 0.68, 0.74, 0.80]
    b = [0.79, 0.75, 0.86, 0.70, 0.69, 0.77]
    result = compare({"team": a, "single": b})
    assert result["means"]["team"] == pytest.approx(sum(a) / len(a))
    ref = paired_t(a, b)
    assert result["paired"]["t"] == pytest.approx(ref["t"])
    assert result["paired"]["a"] == "team"


def test_compare_skips_paired_for_more_than_two():
    result = compare({"x": [1.0], "y": [0.5], "z": [0.0]})
    assert "paired" not in result
    assert set(result["means"]) == {"x", "y", "z"}


def test_agreement_counts_matching_verdicts():
    judge = [0.9, 0.1, 0.8, 0.2]
    human = [1.0, 0.0, 0.3, 0.4]      # third disagrees (judge pass, human fail)
    assert agreement(judge, human) == pytest.approx(0.75)


def test_triple_experiment_ranks_the_systems():
    pytest.importorskip("langgraph")
    from systems.coding_team import ScriptedBrain

    tasks = ["fix the parser", "guard the index", "handle the empty list"]
    # a judge that rewards a real code change over a boilerplate one
    judge = ScriptedJudge(
        lambda task, out: 1.0 if "return" in out else 0.4
    )
    scores = {
        "team": run_suite(team_runner(ScriptedBrain()), tasks, judge),
        "single": run_suite(single_agent_runner(ScriptedBrain()), tasks, judge),
        "workflow": run_suite(workflow_runner(), tasks, judge),
    }
    # the team ships a substantive diff on every task; the fixed pipeline does not
    assert scores["team"] == [1.0, 1.0, 1.0]
    assert scores["workflow"] == [0.4, 0.4, 0.4]
    verdict = compare({"team": scores["team"], "workflow": scores["workflow"]})
    assert verdict["means"]["team"] > verdict["means"]["workflow"]
