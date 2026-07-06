"""Hermetic tests for the architectural-patterns lab (Chapter 21).

No key, no network: every path is a scripted, model-free journal. Each
injection is paired with its detector (True on the break) and a structurally
faithful healthy run (False --- no false positive). The catalogue counts, the
pattern-swap's scorability, and both compositions' emergent failures are
checked too.
"""

from __future__ import annotations

import pytest

from frontier.patterns import compose, injections, signatures
from frontier.patterns.catalogue import (
    CATALOGUE,
    Family,
    debate_run,
    peer_run,
    supervisor_run,
)
from frontier.rig import MESSAGE_SENT, RunResult, four_columns
from frontier.runners import scripted_runner
from frontier.tasks import parallel_task

# (label, broken builder, healthy builder, journal-only detector). The
# misroute is deliberately absent: it is NOT journal-detectable (it needs an
# external eval fact) and is exercised on its own, below.
PAIRS = [
    ("stale_plan", injections.stale_plan_run,
     injections.healthy_plan_run, signatures.is_stale_plan),
    ("placation", injections.placated_run,
     injections.healthy_review_run, signatures.is_placation),
    ("polish_loop", injections.polish_loop_run,
     injections.healthy_review_run, signatures.is_polish_loop),
    ("chorus", injections.chorus_run,
     injections.healthy_debate_run, signatures.is_chorus),
    ("whisper", injections.whisper_run,
     injections.healthy_whisper_run, signatures.is_whisper_divergence),
    ("stampede", injections.stampede_run,
     injections.healthy_dispatch_run, signatures.is_stampede),
    ("stale_read", injections.stale_read_run,
     injections.healthy_read_run, signatures.is_stale_read),
]

# The journal-only detectors: each takes a run and nothing else.
ALL_DETECTORS = [
    signatures.is_stale_plan,
    signatures.is_placation,
    signatures.is_polish_loop,
    signatures.is_chorus,
    signatures.is_whisper_divergence,
    signatures.is_stampede,
    signatures.is_stale_read,
]


@pytest.mark.parametrize("label,broken,healthy,detect", PAIRS,
                         ids=[p[0] for p in PAIRS])
def test_detector_fires_on_break_only(label, broken, healthy, detect):
    assert detect(broken()) is True, f"{label}: missed the injected break"
    assert detect(healthy()) is False, f"{label}: false positive on healthy"


def test_no_detector_fires_on_clean_scripted_run():
    # The strong baseline: a bare scripted runner's journal trips nothing.
    r = scripted_runner()("add a null guard to the parser")
    assert not any(d(r) for d in ALL_DETECTORS)


def test_no_detector_fires_on_clean_injection_run():
    r = injections.clean_run()
    assert not any(d(r) for d in ALL_DETECTORS)


# --- Misroute: judged by the output oracle, never the journal ------------

def _routed_run(specialist: str) -> RunResult:
    """A clean run that merely records routing to ``specialist`` --- the
    honest journal a router writes, carrying no notion of correctness."""
    r = RunResult(task="fix a leak", output="+ x", status="shipped")
    r.log(MESSAGE_SENT, f"routed: specialist={specialist}")
    return r


@pytest.mark.parametrize("routed,correct,expected", [
    ("coding", "security", True),     # routed astray from the required expert
    ("security", "security", False),  # routed to the very expert required
    ("data", "security", True),       # a different wrong specialist
    ("data", "data", False),          # correct, whatever the specialist is
])
def test_misroute_is_the_routed_specialist_against_the_oracle(
        routed, correct, expected):
    # Drive routed and correct INDEPENDENTLY: the detector must recover the
    # routed specialist and compare it to the externally supplied truth. A
    # detector that ignored either input could not pass every row.
    assert signatures.is_misroute(_routed_run(routed), correct) is expected


def test_misroute_flags_injected_break_only_via_oracle():
    correct = injections.CORRECT_SPECIALIST
    assert signatures.is_misroute(injections.misrouted_run(), correct) is True
    assert signatures.is_misroute(
        injections.healthy_routed_run(), correct) is False


def test_misroute_is_journal_invisible():
    # The break and the healthy run have IDENTICAL journals bar the specialist
    # token; no journal-only reading can separate them --- which is the point.
    broken = injections.misrouted_run()
    # Judged against the WRONG oracle (the specialist actually used), even the
    # broken run reads clean: the journal alone never reveals the misroute.
    assert signatures.is_misroute(broken, "coding") is False


# --- Discriminator negatives: the plausible healthy run each detector must
#     NOT flag, once its real discriminator is honoured ---------------------

def test_stampede_silent_on_healthy_fanout():
    # Same trigger, same burst size as a stampede --- but DISTINCT work
    # targets. Duplication is the failure, not breadth.
    assert signatures.is_stampede(injections.healthy_fanout_run()) is False
    # And the injected stampede (same work) still fires.
    assert signatures.is_stampede(injections.stampede_run()) is True


def test_placation_silent_on_converging_review():
    # The healthy review shrinks its diff exactly as a placation does, but
    # closes every objection (open=0) --- shrinking diffs alone must not flag.
    assert signatures.is_placation(injections.healthy_review_run()) is False
    assert signatures.is_placation(injections.placated_run()) is True


def test_polish_loop_silent_on_capped_but_converging_run():
    # The round cap is struck, yet the diffs shrank in earnest: converged,
    # not cycling. Hitting the cap is not itself the failure.
    r = injections.healthy_capped_convergence_run()
    assert signatures.is_polish_loop(r) is False
    assert signatures.is_polish_loop(injections.polish_loop_run()) is True


def test_whisper_silent_on_within_tolerance_rounding():
    # A one-unit gap that technically widens but stays within tolerance is
    # benign rounding, not the whisper game.
    r = injections.healthy_whisper_rounding_run()
    assert signatures.is_whisper_divergence(r) is False
    assert signatures.is_whisper_divergence(injections.whisper_run()) is True


def test_catalogue_has_nine_patterns_and_three_antipatterns():
    patterns = [p for p in CATALOGUE if p.family is not Family.ANTIPATTERN]
    antis = [p for p in CATALOGUE if p.family is Family.ANTIPATTERN]
    assert len(patterns) == 9
    assert len(antis) == 3
    assert all(p.failure_signature.strip() for p in CATALOGUE)


def test_catalogue_covers_the_three_families():
    families = {p.family for p in CATALOGUE}
    assert Family.DELEGATION in families
    assert Family.PROCESS in families
    assert Family.COLLECTIVE in families


@pytest.mark.parametrize("runner", [supervisor_run, peer_run, debate_run])
def test_topology_runners_are_scorable(runner):
    runs = [runner(issue.prompt) for issue in parallel_task()]
    assert all(isinstance(r, RunResult) for r in runs)
    cols = four_columns(runs)
    assert set(cols) == {"quality", "tokens", "latency_s", "failures"}
    assert cols["quality"] > 0
    assert cols["tokens"] > 0


def test_supervisor_of_reflection_has_new_failure():
    r, desc = compose.supervisor_of_reflection()
    # Placation is real one level down ...
    assert signatures.is_placation(r) is True
    # ... yet the composition presents no signature on its face.
    assert not r.failures
    assert desc.strip()


def test_router_over_pipeline_has_new_failure():
    r, desc = compose.router_over_pipeline()
    # The inner misroute survives composition --- but, faithful to the book,
    # it is caught only by the output oracle, never the (green) journal.
    correct = injections.CORRECT_SPECIALIST
    assert signatures.is_misroute(r, correct) is True
    assert signatures.is_misroute(r, "coding") is False   # journal-clean
    assert not r.failures
    assert desc.strip()
