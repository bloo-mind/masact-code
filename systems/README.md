# systems/ — the framework layer

Larger projects built with a modern orchestration framework — principally
[LangGraph](https://langchain-ai.github.io/langgraph/) — demonstrating the
machinery that separates a demonstration from a system: typed state and reducers,
persistence and checkpointing, streaming, human approval and interrupts, tracing,
evaluation, and deployment. They are substantial enough to fail in educationally
useful ways.

Where `foundations/` shows *what the framework is doing on your behalf* in plain
standard-library Python, `systems/` shows the same ideas *at production scale* in
the framework the book teaches. Chapter 23 builds each dependability mechanism
first in plain Python (here in `foundations/`) and then in LangGraph (here); the
correspondence is the point.

## Planned contents

| From | What it builds |
|:-----|:---------------|
| Ch 23 | The coding-agent team hardened: a LangGraph state schema with reducers, a checkpointer, retries with idempotency, a budget treasury, human-gate interrupts, time-travel debugging, and the runnable **chaos-day** script that injects the six failures and confirms they are boring. |
| Ch 24 | The evaluation harness: the **triple experiment** (team vs strong single agent vs fixed workflow), the paired-comparison analysis, ablations, and the LLM-judge calibration notebook. |

## Why it is not here yet

This layer needs an orchestration framework and a model provider, so unlike
`foundations/` it cannot be exercised from the standard library alone, and its
listings are version-dated by the book's standing policy. It is being built after
the foundations layer, which the book's embedded listings depend on directly.

Install its dependencies with:

```bash
uv sync --extra systems
```

See **Appendix C** of the book for setup, keys, and the current state of play.
