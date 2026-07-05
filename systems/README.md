# systems/ — the framework layer

Larger projects built with a modern orchestration framework — principally
[LangGraph](https://langchain-ai.github.io/langgraph/) — demonstrating the
machinery that separates a demonstration from a system: typed state and reducers,
persistence and checkpointing, human approval and interrupts, budgets, retries,
time-travel debugging, and evaluation. They are substantial enough to fail in
educationally useful ways.

Where `foundations/` shows *what the framework is doing on your behalf* in plain
standard-library Python, `systems/` shows the same ideas *in the framework the
book teaches*. Chapter 23 builds each dependability mechanism first in plain
Python (in `foundations/`) and then in LangGraph (here); the correspondence is
the point.

## Contents

| Package | From | What it builds |
|:--------|:-----|:---------------|
| `coding_team/` | Ch 23 | The coding-agent team hardened in LangGraph: a typed `TeamState` with `operator.add` reducers, a checkpointer, a human-gate `interrupt`, a budget treasury, a tester `RetryPolicy` for transient faults, a reviewer→coder revision loop with a turn cap, and time-travel over the checkpoint history. |
| `evaluation/` | Ch 24 | The **triple experiment** — team vs strong single agent vs fixed workflow — run on the same tasks and compared with the paired *t* from `foundations/`, plus the **LLM-as-judge** and its calibration against human labels. |

### The model seam

Every package is built around a model *seam* (`Agent = Model + Harness`, Chapter
3). A `Brain` / `Judge` is a small interface with two implementations:

- a **scripted** one (`ScriptedBrain`, `ScriptedJudge`) — deterministic, no
  model, no key, no network — so the *machinery* (reducers, checkpoints, the
  human gate, budgets, retries, the paired statistics) is exercised hermetically
  in the test suite;
- a **live** one (`LLMBrain`, `LLMJudge`) — a real chat model via
  `langchain-openai`, charging real token usage to the budget.

The graph and the harness are identical either way; only the seam changes. This
is why the whole layer is unit-tested without a key, and why a key is needed only
to watch it drive a real model.

## Run it

Install the extra (its listings are version-dated by the book's standing policy):

```bash
uv sync --extra systems
```

Hermetic — no key required:

```bash
uv run python -m systems.coding_team.run        # the team ships a change
uv run python -m systems.coding_team.chaos_day  # inject the six failures
uv run python -m systems.evaluation.run         # the triple experiment
uv run pytest tests/test_systems_coding_team.py tests/test_systems_evaluation.py
```

`chaos_day` is the Chapter 23 finale: it injects the chapter's six failures —
a crash, a hang, a duplicate delivery, a runaway bill, a mid-run deploy, and a
human breaking in — against the assembled team and confirms each is *boring*.
Six injections, six one-line log entries, none paging a human before nine; a
surprise would be a defect, so it doubles as a test.

Live — needs a key (see **Appendix C** and `.env.example`; put the key in a
git-ignored `.env`, never in a command line or in the repo):

```bash
uv run python -m systems.coding_team.run --live
uv run python -m systems.evaluation.run --live
```

`MASACT_MODEL` selects the chat model (default `gpt-4o-mini`); point `LLMBrain`
at any LangChain chat model to change provider.
