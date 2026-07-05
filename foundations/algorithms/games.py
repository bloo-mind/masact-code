"""Two-player normal-form games, following Appendix A.3's notation.

A game is the tuple <N, (S_i), (u_i)>: two players, a strategy set
S_i for each, and a payoff u_i on every profile (s_i, s_j). We store
the payoffs as a dict keyed by the profile, mapping to the pair
(u_1, u_2) --- row player's payoff first, exactly as @tbl-apa-pd is
laid out. On top of that sit best response, pure-strategy Nash
equilibrium, and the repeated Prisoner's Dilemma with tit-for-tat.

Strategy labels are plain strings so a profile such as
('Defect', 'Defect') is directly comparable, and the module is
stdlib-only.
"""

from collections.abc import Callable
from dataclasses import dataclass

# A behavioural strategy for the repeated game maps (own history,
# opponent history) to the next move.
Strategy = Callable[[list[str], list[str]], str]


@dataclass
class Game:
    """A two-player normal form. ``players`` are the two identifiers;
    ``strategies`` gives each player's S_i; ``payoff`` maps a profile
    (s_i, s_j) to (u_1, u_2)."""

    players: tuple[object, object]
    strategies: dict[object, list[str]]
    payoff: dict[tuple[str, str], tuple[float, float]]


def _payoff_to(game: Game, player: object, s_i: str, s_j: str) -> float:
    # Row player's payoff sits first in the stored pair.
    u_1, u_2 = game.payoff[(s_i, s_j)]
    return u_1 if player == game.players[0] else u_2


def best_responses(
    game: Game, player: object, other_strategy: str
) -> list[str]:
    """BR_i(s_{-i}): the strategies serving ``player`` best while the
    other player holds ``other_strategy`` fixed. Ties are all kept."""
    if player == game.players[0]:  # row player varies s_i
        scored = [
            (s_i, _payoff_to(game, player, s_i, other_strategy))
            for s_i in game.strategies[player]
        ]
    else:  # column player varies s_j
        scored = [
            (s_j, _payoff_to(game, player, other_strategy, s_j))
            for s_j in game.strategies[player]
        ]
    best = max(value for _, value in scored)
    return [s for s, value in scored if value == best]


def pure_nash(game: Game) -> list[tuple[str, str]]:
    """Every pure-strategy Nash equilibrium: profiles in which each
    player is already best-responding to the other."""
    p_1, p_2 = game.players
    equilibria: list[tuple[str, str]] = []
    for s_i in game.strategies[p_1]:
        for s_j in game.strategies[p_2]:
            if (s_i in best_responses(game, p_1, s_j)
                    and s_j in best_responses(game, p_2, s_i)):
                equilibria.append((s_i, s_j))
    return equilibria


def prisoners_dilemma() -> Game:
    """The canonical Prisoner's Dilemma of @tbl-apa-pd: reward 3,
    sucker 0, temptation 5, punishment 1."""
    reward, sucker, temptation, punishment = 3, 0, 5, 1
    labels = ["Cooperate", "Defect"]
    payoff = {
        ("Cooperate", "Cooperate"): (reward, reward),
        ("Cooperate", "Defect"): (sucker, temptation),
        ("Defect", "Cooperate"): (temptation, sucker),
        ("Defect", "Defect"): (punishment, punishment),
    }
    return Game(
        players=(1, 2),
        strategies={1: labels, 2: labels},
        payoff=payoff,
    )


def tit_for_tat(own_history: list[str], opp_history: list[str]) -> str:
    """Cooperate first, then echo the opponent's previous move."""
    if not opp_history:
        return "Cooperate"
    return opp_history[-1]


def always_defect(own_history: list[str], opp_history: list[str]) -> str:
    """Defect unconditionally."""
    return "Defect"


def play_repeated(
    strategy_a: Strategy,
    strategy_b: Strategy,
    rounds: int,
    delta: float = 1.0,
) -> tuple[float, float]:
    """Play the Prisoner's Dilemma for ``rounds`` rounds and return the
    delta-discounted total payoffs (sum_t delta**t u_t), matching the
    economics chapter's discount convention."""
    game = prisoners_dilemma()
    history_a: list[str] = []
    history_b: list[str] = []
    total_a = 0.0
    total_b = 0.0
    for t in range(rounds):
        move_a = strategy_a(history_a, history_b)
        move_b = strategy_b(history_b, history_a)
        u_a, u_b = game.payoff[(move_a, move_b)]
        total_a += delta**t * u_a
        total_b += delta**t * u_b
        history_a.append(move_a)
        history_b.append(move_b)
    return total_a, total_b
