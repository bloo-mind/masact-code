"""The scaling sweep: sizes x topologies, four curves, one flat maximum.

Chapter 27's instrument. It takes a factory that builds a sized, wired team
and runs it across the grid ``SIZES x TOPOLOGIES``, aggregating each cell into
the rig's four columns. Three hypotheses are laid open to refutation:

  (a) a *flat maximum* at a small team size for coupled tasks and later for
      parallel ones --- :func:`flat_maximum` locates the empirical ``n*``;
  (b) cost rising faster than capability past that maximum --- the token
      column;
  (c) failures *migrating* from competence errors to join errors ---
      specification, hand-off, verification --- as the population grows, which
      :func:`failure_census` counts.

The reported *capability* column is the raw Chapter 1 coordination-tax speedup
``speedup(n, p, kappa)`` --- the harvested speedup under the coordination tax,
comparable across regimes, so the parallel curve honestly sits *above* the
coupled one on one shared scale (Chapter 27's claim that capability scales
with the task's parallelism, not with head-count). The scripted factory
(:func:`scaling_scripted_factory`) is calibrated so the sweep *recovers the
theory on its own grid*: the empirical grid maximum equals the theory's
maximum over the same grid ``SIZES`` (see :func:`compare_to_theory`). That
makes the whole lab hermetic --- no key, no network --- while still
demonstrating the method the book cares about. The portable finding is the
method, not the numbers a stand-in prints.
"""

from __future__ import annotations

from collections.abc import Callable

from foundations.algorithms.scaling import speedup

from ..rig import Runner, four_columns, mean
from ..runners import scripted_runner
from ..tasks import coupled_task

# --- The grid --------------------------------------------------------------

SIZES: list[int] = [1, 2, 4, 8]
TOPOLOGIES: list[str] = ["single", "star", "chain", "blackboard", "peer"]

# The two regimes' parallel fractions. Both are chosen so the Chapter 1
# maximiser lands on a grid point --- coupled at n* = 2, parallel at n* = 4,
# so the empirical flat maximum can equal the theoretical one exactly. A
# coupled task divides poorly (low p); a parallel batch divides cleanly.
PARALLEL_P = 0.9
COUPLED_P = 0.2
REGIME_P: dict[str, float] = {"parallel": PARALLEL_P, "coupled": COUPLED_P}

# The task the sweep is run on --- the running example's coupled rename. The
# scripted stand-in ignores its text; a live factory would act on it.
_SWEEP_TASK = coupled_task().prompt
_BASE_TOKENS = 200

# Topology is the wiring that realises the same size on the coordination
# graph. In this scripted stand-in it is a uniform (size-independent) factor,
# so it shifts a topology's whole column without moving its argmax: the
# recovered ``n*`` is the same for every topology, as the size theory demands.
# Broadcast styles (blackboard, peer) coordinate a shade more cheaply; relay
# styles (star, chain) a shade more dearly.
_TOPO_GAIN: dict[str, float] = {
    "single": 1.0, "star": 0.97, "chain": 0.95,
    "blackboard": 1.02, "peer": 1.03,
}
_TOPO_COST: dict[str, float] = {
    "single": 1.0, "star": 1.05, "chain": 1.08,
    "blackboard": 0.98, "peer": 0.95,
}

RunnerFactory = Callable[[int, str], Runner]


# --- The sweep itself ------------------------------------------------------

def scaling_sweep(runner_factory: RunnerFactory, sizes: list[int] = SIZES,
                  topologies: list[str] = TOPOLOGIES, repeats: int = 1,
                  task: str = _SWEEP_TASK) -> dict[tuple[int, str], dict]:
    """Run the grid and aggregate each cell into the four columns.

    ``runner_factory(size, topology)`` returns a :class:`Runner`; each cell is
    run ``repeats`` times and folded with :func:`four_columns`.
    """
    out: dict[tuple[int, str], dict] = {}
    for n in sizes:
        for topo in topologies:
            runner = runner_factory(n, topo)
            runs = [runner(task) for _ in range(repeats)]
            out[(n, topo)] = four_columns(runs)
    return out


def _flat_argmax(sizes: list[int], values: list[float]) -> int:
    """The true argmax of a capability series, tie-broken to the *smallest*
    size --- a genuine flat maximum.

    Real sweeps are noisy: plateaus, ties and sub-threshold wiggles all break
    a walk-until-it-stops-rising rule, which halts at the first plateau and
    under-reports ``n*``. So we take the honest argmax over the swept sizes.
    Because we only advance the incumbent on a *strict* improvement, the first
    (smallest) size achieving the maximum wins the tie, which is the flat
    maximum an engineer wants: the cheapest size that buys the peak.
    """
    best = 0
    for i in range(1, len(values)):
        if values[i] > values[best]:
            best = i
    return sizes[best]


def flat_maximum(sweep: dict[tuple[int, str], dict], topology: str) -> int:
    """The empirical ``n*`` for one topology: the flat maximum (true argmax,
    tie-broken to the smallest size) of its capability curve across the swept
    sizes."""
    series = sorted((n, cell["quality"])
                    for (n, t), cell in sweep.items() if t == topology)
    sizes = [n for n, _ in series]
    values = [q for _, q in series]
    return _flat_argmax(sizes, values)


# --- The failure census ----------------------------------------------------

# The one competence bucket and the three join buckets the book names. A join
# failure is one that only exists because there is more than one agent:
# specification (what to build was under-specified), hand-off (work lost in
# transit), verification (nobody checked the seam).
_JOIN_BUCKETS = ("specification", "handoff", "verification")


def failure_census(runs: list) -> dict[str, int]:
    """Bucket every failure tag on ``runs`` into competence vs the three join
    buckets. Tags are ``"competence"`` or ``"join:<bucket>"``; an unrecognised
    tag is charged to competence, the conservative default."""
    census = {"competence": 0, "specification": 0,
              "handoff": 0, "verification": 0}
    for r in runs:
        for tag in r.failures:
            if tag.startswith("join:"):
                bucket = tag.split(":", 1)[1]
                census[bucket if bucket in census else "handoff"] += 1
            else:
                census["competence"] += 1
    return census


# --- The scripted factory that recovers the theory -------------------------

def _k_comp(n: int) -> int:
    """Competence errors: many when one agent carries the whole task alone,
    fewer as more eyes catch the plain mistakes. Non-increasing in ``n``."""
    return max(0, 6 // n)


def _k_join(n: int) -> int:
    """Join errors: none for a soloist, one more for each extra hand-off the
    growing population introduces. Strictly increasing in ``n``."""
    return max(0, n - 1)


def _join_tag(i: int) -> str:
    """Spread join failures across the three buckets so the census shows the
    whole join family lighting up, not one label."""
    return f"join:{_JOIN_BUCKETS[i % len(_JOIN_BUCKETS)]}"


def scaling_scripted_factory(regime: str,
                             kappa: float = 0.02) -> RunnerFactory:
    """A deterministic factory whose sweep recovers the Chapter 1 theory.

    For team size ``n`` under regime parallel fraction ``p``:

      * the capability column is the raw coordination-tax speedup
        ``speedup(n, p, kappa)`` --- the harvested speedup under the tax,
        comparable across regimes (the parallel curve sits *above* the coupled
        one), so its flat maximum over the swept sizes is exactly the theory's
        maximum over the same grid (see :func:`compare_to_theory`);
      * ``tokens`` rise with the tax ``kappa n(n-1)/2``, so cost keeps
        climbing past the capability peak;
      * ``failures`` migrate: competence errors thin out while join errors
        multiply, so the census shifts from competence- to join-dominated.

    Topology applies a uniform gain/cost factor (see ``_TOPO_GAIN`` /
    ``_TOPO_COST``) that cannot move a column's argmax.
    """
    p = REGIME_P[regime]

    def factory(size: int, topology: str) -> Runner:
        gain = _TOPO_GAIN.get(topology, 1.0)
        cost = _TOPO_COST.get(topology, 1.0)
        # The capability column carried in the rig's ``quality`` slot: the raw
        # coordination-tax speedup, on one scale shared across regimes.
        quality = speedup(size, p, kappa) * gain
        tax = 1 + kappa * size * (size - 1) / 2
        tokens = int(_BASE_TOKENS * tax * cost)
        failures = (["competence"] * _k_comp(size)
                    + [_join_tag(i) for i in range(_k_join(size))])
        status = "shipped" if quality > 0 else "failed"
        return scripted_runner(quality=quality, tokens=tokens,
                               status=status, failures=failures)

    return factory


def compare_to_theory(regime: str, kappa: float = 0.02) -> dict[str, int]:
    """Run the scripted sweep for ``regime`` and compare its empirical flat
    maximum, aggregated across topologies, with the theory's maximum *over the
    same grid*.

    The comparison is honest for *any* ``kappa``: the theory is evaluated on
    the empirical grid ``SIZES`` --- ``argmax`` of ``speedup(n, p, kappa)``
    over ``SIZES`` --- not over a wider ``1..100`` search that the four-point
    sweep could never see. The scripted capability column *is* that same
    speedup, so the empirical grid maximum equals the theory's grid maximum.
    """
    p = REGIME_P[regime]
    sweep = scaling_sweep(scaling_scripted_factory(regime, kappa))
    by_size = [mean([sweep[(n, t)]["quality"] for t in TOPOLOGIES])
               for n in SIZES]
    theoretical_nstar = max(SIZES, key=lambda n: speedup(n, p, kappa))
    return {
        "empirical_nstar": _flat_argmax(SIZES, by_size),
        "theoretical_nstar": theoretical_nstar,
    }
