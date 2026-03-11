"""Tests for iron_butterfly.py — strategy builder."""

import json
import math
from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pytest

import iron_butterfly as ib


# ---------------------------------------------------------------------------
# Unit tests — pure functions (no API calls)
# ---------------------------------------------------------------------------

class TestRoundToStrike:
    def test_exact_multiple(self):
        assert ib.round_to_strike(6780) == 6780

    def test_rounds_up(self):
        assert ib.round_to_strike(6783) == 6785

    def test_rounds_down(self):
        assert ib.round_to_strike(6781) == 6780

    def test_midpoint_rounds_to_nearest(self):
        # Python's round() uses banker's rounding: 6782.5/5 = 1356.5 -> 1356 -> 6780
        assert ib.round_to_strike(6782.5) == 6780

    def test_small_value(self):
        assert ib.round_to_strike(3) == 5

    def test_zero(self):
        assert ib.round_to_strike(0) == 0


class TestParseExpiry:
    def test_today(self):
        result = ib.parse_expiry("today")
        assert result == datetime.now().date()

    def test_today_case_insensitive(self):
        result = ib.parse_expiry("TODAY")
        assert result == datetime.now().date()

    def test_tomorrow(self):
        from datetime import timedelta
        result = ib.parse_expiry("tomorrow")
        assert result == datetime.now().date() + timedelta(days=1)

    def test_explicit_date(self):
        result = ib.parse_expiry("2026-03-11")
        assert result == date(2026, 3, 11)

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError):
            ib.parse_expiry("not-a-date")


class TestMonthCode:
    def test_march_2026(self):
        assert ib.month_code(date(2026, 3, 11)) == "MAR26"

    def test_december_2027(self):
        assert ib.month_code(date(2027, 12, 1)) == "DEC27"


class TestMaturityStr:
    def test_format(self):
        assert ib.maturity_str(date(2026, 3, 11)) == "20260311"


class TestParsePrice:
    def test_none(self):
        assert ib.parse_price(None) is None

    def test_int(self):
        assert ib.parse_price(42) == 42.0

    def test_float(self):
        assert ib.parse_price(42.5) == 42.5

    def test_string_number(self):
        assert ib.parse_price("42.50") == 42.5

    def test_string_with_c_prefix(self):
        assert ib.parse_price("C42.50") == 42.5

    def test_string_with_h_prefix(self):
        assert ib.parse_price("H100.00") == 100.0

    def test_invalid_string(self):
        assert ib.parse_price("N/A") is None

    def test_empty_string(self):
        assert ib.parse_price("") is None


# ---------------------------------------------------------------------------
# API retry tests
# ---------------------------------------------------------------------------

class TestApiRetry:
    @patch("iron_butterfly.requests.get")
    def test_retries_on_500(self, mock_get):
        """Should retry on 500 and succeed on second attempt."""
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"data": "ok"}
        ok_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [fail_resp, ok_resp]

        with patch("iron_butterfly.time.sleep"):
            result = ib.api_get("/test")

        assert result == {"data": "ok"}
        assert mock_get.call_count == 2

    @patch("iron_butterfly.requests.get")
    def test_raises_after_max_retries(self, mock_get):
        """Should raise after exhausting retries."""
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        fail_resp.raise_for_status.side_effect = Exception("500 Server Error")

        mock_get.return_value = fail_resp

        with patch("iron_butterfly.time.sleep"):
            with pytest.raises(Exception, match="500"):
                ib.api_get("/test", retries=2)

        assert mock_get.call_count == 3

    @patch("iron_butterfly.requests.get")
    def test_no_retry_on_4xx(self, mock_get):
        """Should NOT retry on 4xx errors."""
        fail_resp = MagicMock()
        fail_resp.status_code = 400
        fail_resp.raise_for_status.side_effect = Exception("400 Bad Request")

        mock_get.return_value = fail_resp

        with pytest.raises(Exception, match="400"):
            ib.api_get("/test")

        assert mock_get.call_count == 1


# ---------------------------------------------------------------------------
# Strategy construction tests
# ---------------------------------------------------------------------------

class TestBuildStrategy:
    """Test the strategy building logic with mocked API calls."""

    def _mock_api(self, spx_price=6780.0, expiry=date(2026, 3, 11),
                  sp_bid=22.0, sc_bid=22.0, lp_ask=1.0, lc_ask=0.2):
        """Helper to set up mocked API responses for build_strategy."""

        def mock_get_option_contract(strike, right, expiry_date):
            return {"conid": hash((strike, right)) % 10**9, "tradingClass": "SPXW"}

        def mock_get_option_prices(conids):
            prices = {}
            for cid in conids:
                prices[cid] = {"conid": cid, "bid": sp_bid, "ask": sp_bid + 0.2, "last": sp_bid}
            return prices

        return mock_get_option_contract, mock_get_option_prices

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract")
    def test_atm_strikes_below_price(self, mock_contract, mock_prices):
        """ATM strikes should bracket the SPX price."""
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        mock_prices.return_value = {
            12345: {"conid": 12345, "bid": 22.0, "ask": 22.2, "last": 22.0},
        }

        strategy = ib.build_strategy(6783.50, date(2026, 3, 11), ratio=2.0)

        # 6783.50 -> floor to 6780, upper = 6785
        assert strategy["legs"][1]["strike"] == 6780  # Short Put
        assert strategy["legs"][2]["strike"] == 6785  # Short Call

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract")
    def test_wing_width_with_ratio_2(self, mock_contract, mock_prices):
        """Wing width should be ~3x net credit for 2.0 ratio."""
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        # Short bid = 20, so net_credit_shorts = 40
        # wing_width = round_to_strike((2.0 + 1.0) * 40) = round_to_strike(120) = 120
        mock_prices.side_effect = [
            {12345: {"conid": 12345, "bid": 20.0, "ask": 20.2, "last": 20.0}},
            {12345: {"conid": 12345, "bid": 0.5, "ask": 0.6, "last": 0.5}},
        ]

        strategy = ib.build_strategy(6780.0, date(2026, 3, 11), ratio=2.0)
        assert strategy["wing_width"] == 120

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract")
    def test_wing_width_with_lower_ratio(self, mock_contract, mock_prices):
        """Lower ratio should produce tighter wings."""
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        # Short bid = 20, net_credit_shorts = 40
        # ratio=1.5 -> wing_width = round_to_strike(2.5 * 40) = 100
        mock_prices.side_effect = [
            {12345: {"conid": 12345, "bid": 20.0, "ask": 20.2, "last": 20.0}},
            {12345: {"conid": 12345, "bid": 0.5, "ask": 0.6, "last": 0.5}},
        ]

        strategy = ib.build_strategy(6780.0, date(2026, 3, 11), ratio=1.5)
        assert strategy["wing_width"] == 100

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract")
    def test_net_credit_calculation(self, mock_contract, mock_prices):
        """Net credit = short bids - long asks."""
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        # Short legs bid = 20 each -> 40 total
        # Long legs ask = 0.6 each -> 1.2 total
        # Net credit = 40 - 1.2 = 38.8
        mock_prices.side_effect = [
            {12345: {"conid": 12345, "bid": 20.0, "ask": 20.2, "last": 20.0}},
            {12345: {"conid": 12345, "bid": 0.5, "ask": 0.6, "last": 0.5}},
        ]

        strategy = ib.build_strategy(6780.0, date(2026, 3, 11))
        assert strategy["net_credit"] == 38.8
        assert strategy["max_profit"] == 3880.0

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract")
    def test_raises_on_no_bid(self, mock_contract, mock_prices):
        """Should raise if short legs have no bid (market closed)."""
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        mock_prices.return_value = {
            12345: {"conid": 12345, "bid": None, "ask": None, "last": None},
        }

        with pytest.raises(RuntimeError, match="bid prices"):
            ib.build_strategy(6780.0, date(2026, 3, 11))

    @patch("iron_butterfly.get_option_prices")
    @patch("iron_butterfly.get_option_contract")
    def test_four_legs_in_output(self, mock_contract, mock_prices):
        """Strategy should always have exactly 4 legs."""
        mock_contract.return_value = {"conid": 12345, "tradingClass": "SPXW"}
        mock_prices.side_effect = [
            {12345: {"conid": 12345, "bid": 20.0, "ask": 20.2, "last": 20.0}},
            {12345: {"conid": 12345, "bid": 0.5, "ask": 0.6, "last": 0.5}},
        ]

        strategy = ib.build_strategy(6780.0, date(2026, 3, 11))
        assert len(strategy["legs"]) == 4
        actions = [l["action"] for l in strategy["legs"]]
        assert actions == ["BUY", "SELL", "SELL", "BUY"]


# ---------------------------------------------------------------------------
# Order JSON building tests
# ---------------------------------------------------------------------------

class TestBuildOrderJson:
    def test_conidex_format(self):
        strategy = {
            "expiry": "2026-03-11",
            "net_credit": 42.50,
            "max_profit": 4250.0,
            "max_loss": 8750.0,
            "ratio": 2.06,
            "legs": [
                {"action": "BUY", "strike": 6645, "right": "P", "conid": 111, "bid": 1.0, "ask": 1.1, "label": "LP"},
                {"action": "SELL", "strike": 6775, "right": "P", "conid": 222, "bid": 22.0, "ask": 22.2, "label": "SP"},
                {"action": "SELL", "strike": 6780, "right": "C", "conid": 333, "bid": 22.0, "ask": 22.2, "label": "SC"},
                {"action": "BUY", "strike": 6910, "right": "C", "conid": 444, "bid": 0.15, "ask": 0.2, "label": "LC"},
            ],
        }

        result = ib.build_order_json("DUXXXXXXX", strategy, 1)

        assert result["account_id"] == "DUXXXXXXX"
        assert result["orders"][0]["conidex"] == "416904;;;111/1,222/-1,333/-1,444/1"
        assert result["orders"][0]["price"] == -42.50
        assert result["orders"][0]["side"] == "BUY"
        assert result["orders"][0]["quantity"] == 1

    def test_quantity_passed_through(self):
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
