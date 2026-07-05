"""Generative-Agents retrieval scoring: ranking memories by relevance,
recency, and importance (Chapter 7).

The chapter reproduces the ``Memory`` dataclass and ``score`` function
verbatim, so a reader copying the listing from the book finds the identical
code here. ``top_k`` is the small amount of surrounding machinery the chapter
leaves to the companion repository: the sort that turns the score into recall.

Standard library only; nothing here is random, so there is nothing to seed.
"""

from dataclasses import dataclass

@dataclass
class Memory:
    text: str
    rel: float  # components precomputed and normalised to [0, 1]
    rec: float
    imp: float

def score(m: Memory, w_rel: float = 1.0,
          w_rec: float = 0.5, w_imp: float = 0.5) -> float:
    return w_rel * m.rel + w_rec * m.rec + w_imp * m.imp


def top_k(store: list[Memory], k: int, **weights: float) -> list[str]:
    """Texts of the ``k`` highest-scoring memories, best first.

    Any of ``w_rel``, ``w_rec``, ``w_imp`` may be passed to reweight the
    blend exactly as ``score`` does; those omitted keep its defaults.
    """
    ranked = sorted(store, key=lambda m: score(m, **weights),
                    reverse=True)
    return [m.text for m in ranked[:k]]
