"""Tests for the Chapter 7 Generative-Agents retrieval score."""

from pytest import approx

from foundations.algorithms.retrieval import Memory, score, top_k


def _store() -> list[Memory]:
    # The three-memory store printed in Chapter 7.
    return [
        Memory("deploy broke after schema change", 0.9, 0.2, 0.6),
        Memory("user prefers terse replies", 0.3, 0.5, 0.9),
        Memory("staging failed this morning", 0.7, 1.0, 0.4),
    ]


def test_score_is_the_weighted_blend():
    m = Memory("x", 0.9, 0.2, 0.6)
    # 1.0*0.9 + 0.5*0.2 + 0.5*0.6
    assert score(m) == approx(1.3)


def test_book_listing_reproduces_verbatim():
    # The exact expression the Chapter 7 block prints as its result.
    ranked = [m.text for m in
              sorted(_store(), key=score, reverse=True)[:2]]
    assert ranked == ['staging failed this morning',
                      'deploy broke after schema change']


def test_top_k_returns_the_top_two_texts():
    assert top_k(_store(), 2) == ['staging failed this morning',
                                  'deploy broke after schema change']


def test_top_k_with_k_one_returns_the_single_best():
    assert top_k(_store(), 1) == ['staging failed this morning']


def test_weights_forward_to_score():
    # Zero out recency and importance: pure relevance now leads.
    best = top_k(_store(), 1, w_rec=0.0, w_imp=0.0)
    assert best == ['deploy broke after schema change']
