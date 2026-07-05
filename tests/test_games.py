"""Tests for the normal-form games module (Appendix A.3)."""

from foundations.algorithms.games import (
    Game,
    always_defect,
    best_responses,
    play_repeated,
    prisoners_dilemma,
    pure_nash,
    tit_for_tat,
)


def _coordination_game() -> Game:
    # A pure coordination game: agreeing pays, disagreeing does not.
    labels = ["Left", "Right"]
    payoff = {
        ("Left", "Left"): (1, 1),
        ("Left", "Right"): (0, 0),
        ("Right", "Left"): (0, 0),
        ("Right", "Right"): (1, 1),
    }
    return Game(
        players=(1, 2),
        strategies={1: labels, 2: labels},
        payoff=payoff,
    )


def test_pd_best_responses():
    pd = prisoners_dilemma()
    # Defect strictly dominates, so it is the best response to both.
    assert best_responses(pd, 1, "Cooperate") == ["Defect"]
    assert best_responses(pd, 1, "Defect") == ["Defect"]
    assert best_responses(pd, 2, "Cooperate") == ["Defect"]
    assert best_responses(pd, 2, "Defect") == ["Defect"]


def test_pd_unique_nash():
    assert pure_nash(prisoners_dilemma()) == [("Defect", "Defect")]


def test_coordination_has_two_matching_equilibria():
    coord = _coordination_game()
    equilibria = pure_nash(coord)
    # Both matching profiles are equilibria; mismatches are not.
    assert set(equilibria) == {("Left", "Left"), ("Right", "Right")}
    assert ("Left", "Right") not in equilibria
    assert ("Right", "Left") not in equilibria


def test_coordination_best_response_mirrors():
    coord = _coordination_game()
    assert best_responses(coord, 2, "Left") == ["Left"]
    assert best_responses(coord, 2, "Right") == ["Right"]


def test_tit_for_tat_exploited_once_then_mirrors():
    total_tft, total_ad = play_repeated(
        tit_for_tat, always_defect, rounds=10
    )
    # Round 0: tit-for-tat cooperates and is played for the sucker (0)
    # while always-defect takes the temptation (5). From round 1 on
    # tit-for-tat mirrors defection, so both take punishment (1).
    assert total_tft == 0 + 9 * 1  # -> 9
    assert total_ad == 5 + 9 * 1  # -> 14
    # Exploited exactly once: the gap is a single temptation-minus-sucker.
    assert total_ad - total_tft == 5


def test_tit_for_tat_move_rule():
    assert tit_for_tat([], []) == "Cooperate"
    assert tit_for_tat(["Cooperate"], ["Defect"]) == "Defect"
    assert tit_for_tat(["Defect"], ["Cooperate"]) == "Cooperate"
    assert always_defect([], []) == "Defect"


def test_two_defectors_mirror_forever():
    # Two defectors sit at mutual punishment every round.
    total_a, total_b = play_repeated(always_defect, always_defect, 10)
    assert total_a == 10
    assert total_b == 10


def test_discount_factor_matches_geometric_sum():
    # Mutual defection pays 1 each round; delta discounts the stream to
    # 1 + delta + delta**2 = 1.75 at delta = 0.5.
    total_a, total_b = play_repeated(
        always_defect, always_defect, rounds=3, delta=0.5
    )
    assert total_a == 1.75
    assert total_b == 1.75
