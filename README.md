# masact-code

Companion code for the textbook **_Multi-Agent Systems: A Contemporary
Treatment_** by Dell Zhang and Benjamin Chang.

- 📖 Read the book: <https://books.bloo-mind.ai/masact/>
- 💻 This repository: <https://github.com/bloo-mind/masact-code>

The book teaches the concepts and techniques of multi-agent systems in the era
of large language models — taking the classical theory seriously, taking modern
practice seriously, and insisting on connecting the two at every step. This
repository is where that connection is made runnable.

All three layers are **built and tested** — the foundations runtime, the systems
builds (Chapters 23–24), and the frontier labs (Chapters 19/21/22/27) — with a
hermetic test suite that needs no key or network. The frontier labs alone are
**dated by design**: they plug into vendor SDKs that rename their APIs at
leisure, so they record the versions they were last run against and are expected
to need updating. The load-bearing listings printed in the book are faithful
excerpts of the modules here — a line you copy from the page is a line that runs.

## Quick start

The toolchain is the book's own: a recent Python and
[uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/bloo-mind/masact-code.git
cd masact-code
uv sync
uv run pytest            # 138 tests, standard library only
```

Watch the book's running example — the software-engineering team —
resolve a toy task end to end:

```bash
uv run python -m foundations.demo_team
# outcome: shipped | suite: green
```

Every model in that demo is a `FakeClient` replaying a script, so it is
deterministic and spends no tokens. Swap in a real `ModelClient` that calls a
provider, and the same harness drives a live team.

## Layout

Three layers, mirroring the book. The foundations layer runs on the Python
standard library alone; the upper layers need a framework and provider keys and
are built later (see [Appendix C](https://books.bloo-mind.ai/masact/) and each
layer's own README).

### `foundations/` — the runtime and the classics

The from-scratch runtime of **Chapter 20**, module for module:

| Module | Role |
|:-------|:-----|
| `model.py` | the model client behind one interface, plus a `FakeClient` for tests |
| `tools.py` | tools as data; the dispatcher that runs them, errors as observations |
| `context.py` | context assembly — what the model sees, each turn |
| `journal.py` | the append-only event journal; state is a `fold` of it |
| `messages.py` | typed, performative messages (speech acts as an enum) |
| `mailbox.py` | per-agent delivery |
| `budget.py` | the token treasury |
| `agent.py` | the observe–reason–act loop, with three ways to stop |
| `team.py` | the coordinating harness — the merge gate and `run_team` |
| `demo_team.py` | first flight: the whole team on a toy task |

`foundations/algorithms/` — the classical algorithms named across the book,
each with the exact function the book prints plus tests and extensions:

`scaling` (Ch 1, Amdahl for agents) · `tool_schema` (Ch 6) ·
`retrieval` (Ch 7) · `contract_net` (Ch 10) · `lamport`, `dcop` (Ch 11) ·
`games` (Ch 12 / App A) · `jury` (Ch 13) · `argumentation` (Ch 14, Dung) ·
`auctions` (Ch 15, Vickrey + Gode–Sunder) · `shapley` (Ch 16) ·
`dependability` (Ch 23) · `evaluation` (Ch 24) · `calibration` (Ch 26).

`foundations/emergence/` — the Part V simulations, seeded for reproducibility:
`schelling`, `naming_game`, `cascade` (Ch 18).

### `systems/` — the framework layer

Larger LangGraph builds: the hardened coding-agent team and the evaluation
harness of Chapters 23–24. Needs a framework and a provider key. See
[`systems/README.md`](systems/README.md).

### `frontier/` — the moving-target layer

Versioned, dated laboratories on live vendor platforms: the framework
comparison (Ch 19), interoperability (Ch 21–22), and the capstone scaling lab
(Ch 27). See [`frontier/README.md`](frontier/README.md).

## How the book and the code fit together

Not every line belongs in print. The book embeds the small, self-contained
listings that make a concept more straightforward to implement; everything
larger — the LLM-agent harnesses, the experiments, the labs — lives here. The
Chapter 20 runtime excerpts are verbatim slices of the `foundations/` modules;
the standalone listings (the jury sum, exact Shapley, the grounded extension,
the retry-and-gate cores, …) are the exact functions those modules export,
surrounded here by tests and the extensions the chapters leave as exercises.

Requirements: **Python 3.12+**, **uv**. The `foundations/` layer needs no keys;
the upper layers read provider keys from `.env` (copy `.env.example`).

## Contributing

The book invites its readers to argue with the text, flag what is wrong, and
propose the joke the authors ought to have made instead — and the same welcome
extends to the code. Issues and pull requests are gratefully received.

## Citing

```bibtex
@book{zhang2026masact,
  title     = {Multi-Agent Systems: A Contemporary Treatment},
  author    = {Zhang, Dell and Chang, Benjamin},
  year      = {2026},
  url        = {https://books.bloo-mind.ai/masact/}
}
```

## Licence

Released under the [MIT License](LICENSE). Use it, learn from it, build on it.
