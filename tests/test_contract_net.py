"""Tests for the Contract Net simulation (foundations/algorithms)."""

from random import Random

from foundations.algorithms.contract_net import (
    Award, Bidder, FlakyBidder, announce_award, collect_bids, demo,
)


def test_lowest_cost_bidder_wins():
    contractors = [
        Bidder("pricey", cost=9.0),
        Bidder("cheap", cost=2.0),
        Bidder("mid", cost=5.0),
    ]
    award = announce_award("survey the site", contractors)
    assert award.succeeded is True
    assert award.contractor.name == "cheap"
    assert award.attempts == ("cheap",)


def test_declining_contractor_is_skipped():
    contractors = [
        Bidder("busy", cost=None),      # declines the announcement
        Bidder("free", cost=7.0),
    ]
    bids = collect_bids("survey the site", contractors)
    assert [b.contractor.name for b in bids] == ["free"]
    award = announce_award("survey the site", contractors)
    assert award.contractor.name == "free"
    assert "busy" not in award.attempts


def test_failure_reassigns_to_next_best():
    contractors = [
        Bidder("cheap", cost=2.0),
        Bidder("steady", cost=5.0),
        Bidder("dear", cost=9.0),
    ]
    award = announce_award("survey the site", contractors,
                           inject_failures=["cheap"])
    assert award.succeeded is True
    assert award.contractor.name == "steady"
    assert award.attempts == ("cheap", "steady")


def test_all_fail_is_clean_failure():
    contractors = [
        Bidder("a", cost=1.0, reliable=False),
        Bidder("b", cost=2.0, reliable=False),
    ]
    award = announce_award("survey the site", contractors)
    assert isinstance(award, Award)
    assert award.succeeded is False
    assert award.contractor is None
    assert award.attempts == ("a", "b")


def test_no_bidders_at_all_is_clean_failure():
    contractors = [Bidder("busy", cost=None)]
    award = announce_award("survey the site", contractors)
    assert award.succeeded is False
    assert award.contractor is None
    assert award.attempts == ()


def test_flaky_execute_is_seeded_and_deterministic():
    def build():
        rng = Random(0)
        return [
            FlakyBidder("cheap", cost=2.0, fail_prob=0.9, rng=rng),
            Bidder("steady", cost=5.0),
        ]
    first = announce_award("survey the site", build())
    second = announce_award("survey the site", build())
    assert first.contractor.name == second.contractor.name
    assert first.attempts == second.attempts
    # On seed 0 the cheap bidder's draw fails, so steady completes.
    assert first.contractor.name == "steady"
    assert first.attempts == ("cheap", "steady")


def test_demo_reassigns_and_completes():
    award = demo(seed=0)
    assert award.succeeded is True
    assert award.contractor.name == "steady"
    assert award.attempts == ("cheap", "steady")
