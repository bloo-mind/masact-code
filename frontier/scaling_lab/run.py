"""Command-line report for the capstone scaling lab (Chapter 27).

Run ``python -m frontier.scaling_lab.run`` for the hermetic, scripted report:
the sweep table, the empirical-versus-theoretical flat maximum for both
regimes, the failure census at size 1 versus size 8, and the jury ablation.
``--live`` swaps in a real team via the Chapter 23 LangGraph runner as a
best-effort demonstration; it is skipped cleanly if the ``systems`` extra is
not installed.
"""

from __future__ import annotations

import argparse

from ..rig import Runner
from .jury import jury_ablation
from .sweep import (
    SIZES,
    TOPOLOGIES,
    compare_to_theory,
    failure_census,
    scaling_scripted_factory,
    scaling_sweep,
)


def _print_sweep_table(sweep: dict, title: str) -> None:
    print(f"\n{title}")
    header = "  topology     " + "".join(f"  n={n:<10}" for n in SIZES)
    print("  (cap = capability: harvested speedup, shared scale across "
          "regimes)")
    print(header)
    for topo in TOPOLOGIES:
        cells = []
        for n in SIZES:
            c = sweep[(n, topo)]
            cells.append(f"cap={c['quality']:.3f} t={int(c['tokens']):>4}")
        print(f"  {topo:<11}" + "  ".join(f"{c:<12}" for c in cells))


def _print_flat_maximum() -> None:
    print("\nflat maximum: empirical (swept) vs theory's maximum over the "
          "same grid")
    for regime in ("coupled", "parallel"):
        cmp = compare_to_theory(regime)
        mark = "match" if (cmp["empirical_nstar"]
                           == cmp["theoretical_nstar"]) else "MISMATCH"
        print(f"  {regime:<9} empirical n*={cmp['empirical_nstar']}  "
              f"theoretical n*={cmp['theoretical_nstar']}  [{mark}]")


def _print_census() -> None:
    print("\nfailure census (across topologies): size 1 vs size 8")
    factory = scaling_scripted_factory("parallel")
    for size in (1, 8):
        runs = [factory(size, t)(task="") for t in TOPOLOGIES]
        c = failure_census(runs)
        join = c["specification"] + c["handoff"] + c["verification"]
        print(f"  size {size}: competence={c['competence']:>3}  "
              f"join={join:>3} "
              f"(spec={c['specification']} hand={c['handoff']} "
              f"verify={c['verification']})")


def _print_jury() -> None:
    print("\njury ablation: accuracy rises as error-correlation falls")
    print("  stage           disagree   rho    n_eff   accuracy")
    for s in jury_ablation():
        print(f"  {s.label:<14} {s.disagreement:>7.3f}  "
              f"{s.correlation:>5.3f}  {s.effective_n:>5.2f}  "
              f"{s.accuracy:>7.3f}")


def _live_factory():
    """Best-effort live factory: the Chapter 23 team on a real model, its
    size/topology ignored (the graph is not itself sized, so this is a smoke,
    not a true sized sweep). Raises if the ``systems`` extra or a key is
    absent, so the caller can skip cleanly."""
    from dotenv import load_dotenv

    from systems.coding_team import LLMBrain

    from ..runners import langgraph_runner
    load_dotenv()                         # ANTHROPIC_API_KEY from a .env
    brain = LLMBrain()

    def factory(size: int, topology: str) -> Runner:
        return langgraph_runner(brain)

    return factory


def _run_live() -> None:
    print("\n--- live sweep (Chapter 23 LangGraph team, best-effort) ---")
    try:
        factory = _live_factory()
        sweep = scaling_sweep(factory, sizes=[1, 2], topologies=["single"])
    except Exception as exc:  # noqa: BLE001 -- report and carry on
        print(f"  live sweep unavailable: {exc}")
        return
    _print_sweep_table(sweep, "live sweep (partial grid)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="also run a best-effort live LangGraph sweep")
    args = parser.parse_args()

    print("=== Chapter 27: the capstone scaling lab (scripted) ===")
    for regime in ("coupled", "parallel"):
        sweep = scaling_sweep(scaling_scripted_factory(regime))
        _print_sweep_table(sweep, f"sweep: {regime} regime")
    _print_flat_maximum()
    _print_census()
    _print_jury()

    if args.live:
        _run_live()


if __name__ == "__main__":
    main()
