"""Tests for iron_butterfly.py — strategy builder."""

from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pytest

import iron_butterfly as ib


# ---------------------------------------------------------------------------
# Unit tests — pure functions
# ---------------------------------------------------------------------------

class TestRoundToStrike:
    def test_exact_multiple(self) -> None:
        assert ib.round_to_strike(6780) == 6780

    def test_rounds_up(self) -> None:
        assert ib.round_to_strike(6783) == 6785

    def test_rounds_down(self) -> None:
        assert ib.round_to_strike(6781) == 6780

    def test_midpoint_rounds_to_nearest(self) -> None:
        # Python's round() uses banker's rounding: 6782.5/5 = 1356.5 -> 1356 -> 6780
        assert ib.round_to_strike(6782.5) == 6780

    def test_small_value(self) -> None:
        assert ib.round_to_strike(3) == 5

    def test_zero(self) -> None:
        assert ib.round_to_strike(0) == 0


class TestParseExpiry:
    def test_today(self) -> None:
        result = ib.parse_expiry("today")
        assert result == datetime.now().date()

    def test_today_case_insensitive(self) -> None:
        result = ib.parse_expiry("TODAY")
        assert result == datetime.now().date()

    def test_tomorrow(self) -> None:
        from datetime import timedelta
        result = ib.parse_expiry("tomorrow")
        assert result == datetime.now().date() + timedelta(days=1)

    def test_explicit_date(self) -> None:
        result = ib.parse_expiry("2026-03-11")
        assert result == date(2026, 3, 11)

    def test_invalid_date_raises(self) -> None:
        with pytest.raises(ValueError):
            ib.parse_expiry("not-a-date")


class TestMonthCode:
    def test_march_2026(self) -> None:
        assert ib.month_code(date(2026, 3, 11)) == "MAR26"

    def test_december_2027(self) -> None:
        assert ib.month_code(date(2027, 12, 1)) == "DEC27"


class TestMaturityStr:
    def test_format(self) -> None:
        assert ib.maturity_str(date(2026, 3, 11)) == "20260311"


# ---------------------------------------------------------------------------
# Strategy construction tests
# ---------------------------------------------------------------------------

class TestBuildStrategy:
    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract_for_expiry")
    def test_atm_strikes_below_price(self, mock_contract: MagicMock, mock_prices: MagicMock) -> None:
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        mock_prices.return_value = {
            12345: {"bid": 22.0, "ask": 22.2, "last": 22.0},
        }

        strategy = ib.build_strategy(6783.50, date(2026, 3, 11), ratio=2.0)
        assert strategy["legs"][1]["strike"] == 6780  # Short Put
        assert strategy["legs"][2]["strike"] == 6785  # Short Call

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract_for_expiry")
    def test_wing_width_with_ratio_2(self, mock_contract: MagicMock, mock_prices: MagicMock) -> None:
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        mock_prices.side_effect = [
            {12345: {"bid": 20.0, "ask": 20.2, "last": 20.0}},
            {12345: {"bid": 0.5, "ask": 0.6, "last": 0.5}},
        ]

        strategy = ib.build_strategy(6780.0, date(2026, 3, 11), ratio=2.0)
        assert strategy["wing_width"] == 120

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract_for_expiry")
    def test_wing_width_with_lower_ratio(self, mock_contract: MagicMock, mock_prices: MagicMock) -> None:
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        mock_prices.side_effect = [
            {12345: {"bid": 20.0, "ask": 20.2, "last": 20.0}},
            {12345: {"bid": 0.5, "ask": 0.6, "last": 0.5}},
        ]

        strategy = ib.build_strategy(6780.0, date(2026, 3, 11), ratio=1.5)
        assert strategy["wing_width"] == 100

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract_for_expiry")
    def test_net_credit_calculation(self, mock_contract: MagicMock, mock_prices: MagicMock) -> None:
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        mock_prices.side_effect = [
            {12345: {"bid": 20.0, "ask": 20.2, "last": 20.0}},
            {12345: {"bid": 0.5, "ask": 0.6, "last": 0.5}},
        ]

        strategy = ib.build_strategy(6780.0, date(2026, 3, 11))
        assert strategy["net_credit"] == 38.8
        assert strategy["max_profit"] == 3880.0

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract_for_expiry")
    def test_raises_on_no_bid(self, mock_contract: MagicMock, mock_prices: MagicMock) -> None:
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        mock_prices.return_value = {
            12345: {"bid": None, "ask": None, "last": None},
        }

        with pytest.raises(RuntimeError, match="bid prices"):
            ib.build_strategy(6780.0, date(2026, 3, 11))

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract_for_expiry")
    def test_four_legs_in_output(self, mock_contract: MagicMock, mock_prices: MagicMock) -> None:
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        mock_prices.side_effect = [
            {12345: {"bid": 20.0, "ask": 20.2, "last": 20.0}},
            {12345: {"bid": 0.5, "ask": 0.6, "last": 0.5}},
        ]

        strategy = ib.build_strategy(6780.0, date(2026, 3, 11))
        assert len(strategy["legs"]) == 4
        actions = [leg["action"] for leg in strategy["legs"]]
        assert actions == ["BUY", "SELL", "SELL", "BUY"]


# ---------------------------------------------------------------------------
# Order JSON building tests
# ---------------------------------------------------------------------------

class TestBuildOrderJson:
    def test_conidex_format(self) -> None:
        strategy = {
            "expiry": "2026-03-11", "net_credit": 42.50,
            "max_profit": 4250.0, "max_loss": 8750.0, "ratio": 2.06,
            "legs": [
                {"action": "BUY", "strike": 6645, "right": "P", "conid": 111, "bid": 1.0, "ask": 1.1, "label": "LP"},
                {"action": "SELL", "strike": 6775, "right": "P", "conid": 222, "bid": 22.0, "ask": 22.2, "label": "SP"},
                {"action": "SELL", "strike": 6780, "right": "C", "conid": 333, "bid": 22.0, "ask": 22.2, "label": "SC"},
                {"action": "BUY", "strike": 6910, "right": "C", "conid": 444, "bid": 0.15, "ask": 0.2, "label": "LC"},
            ],
        }

        result = ib.build_order_json("DUXXXXXXX", strategy, 1)
        assert result["orders"][0]["conidex"] == "416904;;;111/1,222/-1,333/-1,444/1"
        assert result["orders"][0]["price"] == -42.50
        assert result["orders"][0]["orderType"] == "LMT"

    def test_quantity_passed_through(self) -> None:
        strategy = {
            "expiry": "2026-03-11", "net_credit": 10.0, "max_profit": 1000, "max_loss": 2000, "ratio": 2.0,
            "legs": [
                {"action": "BUY", "conid": 1, "strike": 100, "right": "P", "bid": 1, "ask": 1, "label": "L"},
                {"action": "SELL", "conid": 2, "strike": 200, "right": "P", "bid": 10, "ask": 10, "label": "S"},
                {"action": "SELL", "conid": 3, "strike": 300, "right": "C", "bid": 10, "ask": 10, "label": "S"},
                {"action": "BUY", "conid": 4, "strike": 400, "right": "C", "bid": 1, "ask": 1, "label": "L"},
            ],
        }

        result = ib.build_order_json("DUXXXXXXX", strategy, 5)
        assert result["orders"][0]["quantity"] == 5
