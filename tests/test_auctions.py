"""Tests for the Chapter 15 auctions module."""

from foundations.algorithms.auctions import (
    best_response_second_price,
    first_price,
    second_price,
    zi_double_auction,
)


def test_second_price_runner_up_price():
    assert second_price({"a": 10, "b": 7, "c": 4}) == ("a", 7)


def test_first_price_charges_own_bid():
    assert first_price({"a": 10, "b": 7, "c": 4}) == ("a", 10)


def test_second_price_ties_break_deterministically():
    # A tie at the top means the price equals the tied value.
    assert second_price({"a": 10, "b": 10, "c": 4}) == ("a", 10)


def test_second_price_single_bidder_pays_nothing():
    # No runner-up envelope, so no externality to charge.
    assert second_price({"a": 5}) == ("a", 0.0)


def test_truthful_is_weakly_optimal_when_value_beats_field():
    assert best_response_second_price(10, [7, 4]) is True


def test_truthful_is_weakly_optimal_when_value_below_field():
    assert best_response_second_price(3, [7, 4]) is True


def test_truthful_is_weakly_optimal_at_the_knife_edge():
    assert best_response_second_price(7, [7, 4]) is True


def test_truthful_is_weakly_optimal_against_empty_field():
    assert best_response_second_price(5, []) is True


def test_zi_double_auction_reaches_high_efficiency():
    buyer_values = [10, 9, 8, 7, 6]
    seller_costs = [2, 3, 4, 5, 6]
    eff = zi_double_auction(buyer_values, seller_costs, 200, 7)
    # Gode--Sunder: budget-constrained random traders clear almost
    # all the available surplus.
    assert eff >= 0.9
    assert eff <= 1.0


def test_zi_double_auction_is_deterministic_under_seed():
    buyer_values = [10, 9, 8, 7, 6]
    seller_costs = [2, 3, 4, 5, 6]
    first = zi_double_auction(buyer_values, seller_costs, 200, 3)
    again = zi_double_auction(buyer_values, seller_costs, 200, 3)
    assert first == again


def test_zi_double_auction_efficiency_across_seeds():
    buyer_values = [10, 9, 8, 7, 6]
    seller_costs = [2, 3, 4, 5, 6]
    for seed in range(10):
        eff = zi_double_auction(
            buyer_values, seller_costs, 200, seed
        )
        assert eff >= 0.9
