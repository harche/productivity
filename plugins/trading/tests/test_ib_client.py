"""Tests for ib_client helper functions."""

from unittest.mock import MagicMock
from ib_client import round_to_tick, find_option_by_delta, build_combo
from ib_async import Contract, ComboLeg


class TestRoundToTick:
    def test_rounds_up(self):
        assert round_to_tick(1.23) == 1.25

    def test_rounds_down(self):
        assert round_to_tick(1.22) == 1.20

    def test_exact(self):
        assert round_to_tick(1.25) == 1.25

    def test_negative(self):
        assert round_to_tick(-72.17) == -72.15

    def test_zero(self):
        assert round_to_tick(0.0) == 0.0

    def test_custom_tick(self):
        assert round_to_tick(1.23, tick=0.01) == 1.23


class TestFindOptionByDelta:
    def _make_ticker(self, strike, right, delta):
        t = MagicMock()
        t.contract = MagicMock()
        t.contract.right = right
        t.contract.strike = strike
        t.modelGreeks = MagicMock()
        t.modelGreeks.delta = delta
        return t

    def test_finds_closest_put(self):
        tickers = [
            self._make_ticker(7400, "P", -0.30),
            self._make_ticker(7450, "P", -0.15),
            self._make_ticker(7500, "P", -0.05),
        ]
        result = find_option_by_delta(tickers, 0.15, "P")
        assert result.contract.strike == 7450

    def test_finds_closest_call(self):
        tickers = [
            self._make_ticker(7500, "C", 0.50),
            self._make_ticker(7550, "C", 0.30),
            self._make_ticker(7600, "C", 0.10),
        ]
        result = find_option_by_delta(tickers, 0.50, "C")
        assert result.contract.strike == 7500

    def test_filters_by_side(self):
        tickers = [
            self._make_ticker(7400, "P", -0.50),
            self._make_ticker(7500, "C", 0.50),
        ]
        result = find_option_by_delta(tickers, 0.50, "C")
        assert result.contract.right == "C"

    def test_skips_none_greeks(self):
        t = MagicMock()
        t.contract.right = "C"
        t.modelGreeks = None
        result = find_option_by_delta([t], 0.50, "C")
        assert result is None

    def test_empty_list(self):
        assert find_option_by_delta([], 0.50, "C") is None


class TestBuildCombo:
    def test_builds_bag_contract(self):
        c1 = Contract(conId=100, exchange="SMART")
        c2 = Contract(conId=200, exchange="SMART")
        bag = build_combo("SPX", [(c1, "BUY"), (c2, "SELL")])
        assert bag.secType == "BAG"
        assert bag.symbol == "SPX"
        assert len(bag.comboLegs) == 2

    def test_leg_actions(self):
        c1 = Contract(conId=100, exchange="SMART")
        c2 = Contract(conId=200, exchange="SMART")
        bag = build_combo("SPX", [(c1, "BUY"), (c2, "SELL")])
        assert bag.comboLegs[0].action == "BUY"
        assert bag.comboLegs[1].action == "SELL"

    def test_leg_conids(self):
        c1 = Contract(conId=111, exchange="SMART")
        c2 = Contract(conId=222, exchange="SMART")
        bag = build_combo("SPX", [(c1, "BUY"), (c2, "SELL")])
        assert bag.comboLegs[0].conId == 111
        assert bag.comboLegs[1].conId == 222

    def test_four_legs(self):
        legs = [
            (Contract(conId=i, exchange="SMART"), "BUY" if i % 2 == 0 else "SELL")
            for i in range(4)
        ]
        bag = build_combo("SPX", legs)
        assert len(bag.comboLegs) == 4
