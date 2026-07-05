# masact-code

Companion code for the textbook **_Multi-Agent Systems: A Contemporary
Treatment_** by Dell Zhang and Benjamin Chang.

- 📖 Read the book: <https://books.bloo-mind.ai/masact/>
- 💻 This repository: <https://github.com/bloo-mind/masact-code>

The book teaches the concepts and techniques of multi-agent systems in the era
of large language models — taking the classical theory seriously, taking modern
practice seriously, and insisting on connecting the two at every step. This
repository is where that connection is made runnable.

> **Status: early scaffolding.** The book is being written in public, and this
> repository is filling in alongside it. The layout below is the destination;
> expect directories to appear as the corresponding chapters settle. The
> load-bearing listings already live *in the book itself* — this repository
> carries the full modules and the larger programmes around them.

## How the book and the code fit together

Not every line belongs in print. The book embeds the small, self-contained
listings that make a concept more straightforward to implement — a Lamport
clock, the jury-theorem sum, an exact Shapley value, the core of the from-scratch
runtime. Everything larger — the full modules, the LLM-agent harnesses, the
experiments, the labs — lives here, referenced from the text but not shown in
it. **Appendix C** of the book is the setup guide; this README is its front door.

Throughout, one project runs as the book's spine: an autonomous
**software-engineering team** — an orchestrator that decomposes a task, one or
more coder agents, a reviewer, and a tester, working over a real repository
under a bounded budget of tokens and time. It is cooperative in its mission and
competitive in its use of scarce compute, which is why it spans both halves of
the field.

## Layout

The repository is organised in three layers, mirroring the book.

| Layer | What it holds | Dependencies |
|:------|:--------------|:-------------|
| `foundations/` | Small, transparent implementations of the algorithms and mechanisms discussed in the book — kept dependency-light so you can see what the code is doing and what it is assuming. The from-scratch runtime built in Chapter 20 lives here. | Standard library, mostly |
| `systems/` | Larger projects built with a modern orchestration framework — principally [LangGraph](https://langchain-ai.github.io/langgraph/) — demonstrating typed state, persistence, streaming, human approval, tracing, evaluation, and deployment. Substantial enough to fail in educationally useful ways. | A framework, model APIs |
| `frontier/` | Versioned online laboratories involving current commercial and open-source agent platforms, including coding-agent teams. Maintained separately because these platforms rename their APIs at leisure. | Vendor SDKs, live keys |

The dividing line is deliberate: the `foundations/` layer is meant to outlast
every framework and vendor in the book, so it depends on as little as possible;
the `frontier/` layer carries the burden of currency, so that a reader meeting
the fifth renamed version of an API is not thereby obliged to purchase a new
theory of cooperation.

## Requirements

- **Python 3.12+**
- [**uv**](https://docs.astral.sh/uv/) for environment and dependency management,
  matching the book's toolchain.
- For the `systems/` and `frontier/` layers, API keys for one or more model
  providers. The `foundations/` layer needs none.

Once the package layout lands, getting started will be the usual two lines:

```bash
git clone https://github.com/bloo-mind/masact-code.git
cd masact-code && uv sync
```

Exact run instructions per layer will accompany the code as it arrives; see
Appendix C of the book for the current setup guide.

## Contributing

The book invites its readers to argue with the text, flag what is wrong, and
propose the joke the authors ought to have made instead — and the same welcome
extends to the code. Issues and pull requests are gratefully received.

## Citing

If this book or its code is useful in your work, please cite:

```bibtex
@book{zhang2026masact,
  title     = {Multi-Agent Systems: A Contemporary Treatment},
  author    = {Zhang, Dell and Chang, Benjamin},
  year      = {2026},
  url       = {https://books.bloo-mind.ai/masact/}
}
```

## Licence

Released under the [MIT License](LICENSE). Use it, learn from it, build on it.
