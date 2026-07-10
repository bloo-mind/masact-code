# frontier/ — the moving-target layer

Versioned online laboratories on current agent platforms. This layer carries the
burden of currency, so that a reader who meets the fifth renamed version of an
API is not thereby obliged to purchase a new theory of cooperation. The durable
content is the **method** — the four columns, the flat maximum, the failure
census — not the numbers; the numbers date, and are meant to.

Everything is an instrument over one **shared measurement rig** ([rig.py](rig.py)):
a `Runner` turns a task into a `RunResult` carrying the four columns the book
reuses everywhere — quality, tokens, latency, and failure behaviour — plus an
append-only **journal** in the Chapter 20 event vocabulary, because every failure
signature the book names is defined as something legible *in the journal*, not
eyeballed in the artefact. The runners ([runners.py](runners.py)) are the dated
seam: a scripted runner makes the whole layer testable with **no key and no
network**, and live runners plug a real framework or vendor SDK in behind the
same interface.

## The labs

| Lab | From | What it builds |
|:----|:-----|:---------------|
| [`scaling_lab/`](scaling_lab/) | Ch 27 | The **capstone**. Sweeps team size × topology; locates the empirical flat maximum and checks it against the Amdahl-with-coordination-tax theory (`foundations.scaling`) on the same grid; shows cost rising past the maximum and the failure census migrating competence → join as the population grows. Plus the diversity-ablation twin: a jury switching on as measured error-correlation falls. |
| [`framework_lab/`](framework_lab/) | Ch 19 | One coding job scored across the book's three design-space positions — a **graph runtime** (LangGraph), a **vendor agent SDK** (Claude Agent SDK), and a **declarative crew** (CrewAI) — plus the standing plain baseline, all on the **same model**. The lines-of-code column spreads dramatically and misleads (declaration wins it); the **failure-behaviour** column is the separator that repays the exercise — the census *enacts* each runner's declared, dated fault disposition (tool error / timeout / malformed response) into an observable run and reads the verdict back off the run, never off a name → verdict table; the dispositions themselves remain explicit assumptions until a live adapter is probed and its observed policy attached, which is exactly what the Chapter 19 exercises do. |
| [`interop/`](interop/) | Ch 22 | The three altitudes. An **MCP** server wrapping a team tool, called over the protocol (in-memory for tests, stdio for real); an **A2A Agent Card** published at its well-known address, with the task lifecycle; and the supervisor-meets-supervisor deadlock — every message schema-valid while the joint system makes no progress: *schemas green, task dead*. |
| [`patterns/`](patterns/) | Ch 21 | The pattern catalogue (nine patterns, three anti-patterns) and a **journal detector** for each characteristic failure — stale plan, placation, polish loop, chorus, whisper divergence, stampede, stale read — each firing on its injection and staying silent on a healthy run. The router's *misroute* is the honest exception: it is invisible in the journal (a healthy run of the wrong kind), so it is judged by an output oracle. Plus composition: a supervisor of reflection launders placation up the hierarchy; a router over a pipeline turns a wrong answer into a wrong process. |

## Running the labs

Hermetic — **no key, no network** (scripted runners / in-process MCP):

```bash
uv run python -m frontier.scaling_lab.run     # the capstone sweep + jury
uv run python -m frontier.framework_lab.run   # the four-column scorecard
uv run python -m frontier.interop.run         # MCP round-trip + Agent Card + deadlock
uv run python -m frontier.patterns.run        # pattern-swap + failure detectors
uv run pytest tests/test_frontier_*.py
```

Live — needs a key in a git-ignored `.env` (see **Appendix C**):

```bash
uv run python -m frontier.framework_lab.run --live   # langgraph vs plain on one real model
uv run python -m frontier.scaling_lab.run --live     # a small real-team smoke
```

## Dated against (2026-07)

- `mcp` **1.26.0** (as pinned in `uv.lock`) — the tool interface; `FastMCP` + the in-memory test transport.
- `langgraph` / `langchain-anthropic` — the graph runtime and model seam (shared
  with `systems/`, installed via the `systems` extra).
- `claude-agent-sdk` **0.2.110** — the vendor-agent-SDK position. It drives the
  `claude` CLI as its runtime, so it needs that binary on `PATH`; the adapter
  runs it with no tools and `setting_sources=[]` so the spawned CLI ignores the
  host's own settings, hooks, and plugins (whose events otherwise flood the turn
  budget). It is the slowest position by a wide margin — CLI-spawn overhead — and
  the framework scorecard records a crashing framework as a failure-behaviour
  data point rather than falling over.
- `crewai` **1.15.1** — the declarative-crew position. Heavy (pulls litellm and
  friends), and runs the shared Claude model through litellm's `anthropic/<model>`
  for same-model control. Telemetry is opted out in the runner.
- The **A2A Agent Card** is built to the published JSON spec directly (a
  dataclass → `/.well-known/agent-card.json`) rather than via `a2a-sdk`, whose
  1.x line is protobuf-shaped.

Install with `uv sync --extra frontier`. Expect the version-dated runners to need
updating; that is the nature of the frontier, and the reason the theory lives in
`foundations/` and the book.
