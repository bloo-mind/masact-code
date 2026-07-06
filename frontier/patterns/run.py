"""CLI for the architectural-patterns lab (Chapter 21).

Three acts, matching the chapter:

1. *The pattern-swap* --- the same batch routed through supervisor, peer, and
   debate topologies, scored once on the rig's four columns.
2. *The failure census* --- break each pattern its own way and let the paired
   detector identify it from the journal alone.
3. *Composition voids warranties* --- one composition and the new failure mode
   neither pattern has alone.

Run: ``python -m frontier.patterns.run``. Deterministic; no key, no network.
"""

from __future__ import annotations

from ..rig import Runner, four_columns, run_timed
from ..tasks import parallel_task
from . import compose, injections, signatures
from .catalogue import CATALOGUE, Family, debate_run, peer_run, supervisor_run


def _swap() -> None:
    print("== Pattern-swap: one batch, three topologies ==")
    batch = parallel_task()
    swaps: dict[str, Runner] = {
        "supervisor": supervisor_run,
        "peer": peer_run,
        "debate": debate_run,
    }
    print(f"  {'topology':<12}{'quality':>9}{'tokens':>9}"
          f"{'latency_s':>11}{'failures':>10}")
    for name, runner in swaps.items():
        runs = [run_timed(lambda r=runner, i=issue: r(i.prompt))
                for issue in batch]
        c = four_columns(runs)
        print(f"  {name:<12}{c['quality']:>9.2f}{c['tokens']:>9.0f}"
              f"{c['latency_s']:>11.4f}{c['failures']:>10.0f}")


def _census() -> None:
    print("\n== Failure census: identify each from the journal alone ==")
    # The misroute is the exception the chapter insists on: a perfectly
    # healthy run of the wrong kind, invisible in the journal. It is judged
    # not from the trace but from an external eval fact --- the specialist the
    # task actually required --- so it is scored on its own, below the census.
    _misroute_census()
    cases = [
        ("planner-executor / stale plan", injections.stale_plan_run,
         signatures.is_stale_plan),
        ("reflection / placation", injections.placated_run,
         signatures.is_placation),
        ("reflection / polish loop", injections.polish_loop_run,
         signatures.is_polish_loop),
        ("debate / chorus", injections.chorus_run, signatures.is_chorus),
        ("hierarchical / whisper", injections.whisper_run,
         signatures.is_whisper_divergence),
        ("blackboard / stampede", injections.stampede_run,
         signatures.is_stampede),
        ("blackboard / stale read", injections.stale_read_run,
         signatures.is_stale_read),
    ]
    healthy = injections.clean_run()
    for label, inject, detect in cases:
        flagged = detect(inject())
        clean = detect(healthy)
        mark = "FLAGGED" if flagged else "missed"
        print(f"  {label:<32}broken={mark:<8}healthy={clean}")


def _misroute_census() -> None:
    """Score the misroute against the output oracle, not the journal."""
    correct = injections.CORRECT_SPECIALIST
    broken = signatures.is_misroute(injections.misrouted_run(), correct)
    healthy = signatures.is_misroute(injections.healthy_routed_run(), correct)
    mark = "FLAGGED" if broken else "missed"
    print(f"  {'router / misroute (oracle)':<32}"
          f"broken={mark:<8}healthy={healthy}")
    print("    note: journal-invisible --- judged by the correct specialist "
          "(an external eval fact), not the trace")


def _composition() -> None:
    print("\n== Composition voids warranties ==")
    r, desc = compose.supervisor_of_reflection()
    inner = signatures.is_placation(r)
    print(f"  supervisor-of-reflection: inner placation detected={inner}")
    print(f"    {desc}")
    r2, desc2 = compose.router_over_pipeline()
    inner2 = signatures.is_misroute(r2, injections.CORRECT_SPECIALIST)
    print(f"  router-over-pipeline: inner misroute detected={inner2} "
          f"(via output oracle, not the journal)")
    print(f"    {desc2}")


def _catalogue() -> None:
    patterns = [p for p in CATALOGUE if p.family is not Family.ANTIPATTERN]
    antis = [p for p in CATALOGUE if p.family is Family.ANTIPATTERN]
    print("== Catalogue ==")
    print(f"  {len(patterns)} patterns in three families, "
          f"{len(antis)} anti-patterns")


def main() -> None:
    _catalogue()
    print()
    _swap()
    _census()
    _composition()


if __name__ == "__main__":
    main()
