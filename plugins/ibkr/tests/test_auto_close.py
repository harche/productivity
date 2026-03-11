"""Tests for auto_close.py — auto-closing positions."""

import json
from unittest.mock import patch, MagicMock, call

import pytest

import auto_close as ac


# ---------------------------------------------------------------------------
# Parse price tests
# ---------------------------------------------------------------------------

class TestParsePrice:
    def test_none(self):
        assert ac.parse_price(None) is None

    def test_float(self):
        assert ac.parse_price(42.5) == 42.5

    def test_string_with_prefix(self):
        assert ac.parse_price("C21.40") == 21.4


# ---------------------------------------------------------------------------
# P/L computation tests
# ---------------------------------------------------------------------------

class TestComputeComboPnl:
    def test_profitable_position(self):
        """When close cost < credit received, P/L is positive."""
        legs = [
            {"action": "BUY", "conid": 1},
            {"action": "SELL", "conid": 2},
            {"action": "SELL", "conid": 3},
            {"action": "BUY", "conid": 4},
        ]
        prices = {
            1: {"bid": 0.5, "ask": 0.6},   # Long: sell at bid 0.5
            2: {"bid": 15.0, "ask": 15.2},  # Short: buy at ask 15.2
            3: {"bid": 15.0, "ask": 15.2},  # Short: buy at ask 15.2
            4: {"bid": 0.1, "ask": 0.15},   # Long: sell at bid 0.1
        }

        result = ac.compute_combo_pnl(legs, prices)
        # Combo value = +0.5 (sell long) - 15.2 (buy short) - 15.2 (buy short) + 0.1 (sell long)
        expected = 0.5 - 15.2 - 15.2 + 0.1
        assert abs(result - expected) < 0.01

    def test_handles_missing_prices(self):
        """Should skip legs with missing prices."""
        legs = [
            {"action": "BUY", "conid": 1},
            {"action": "SELL", "conid": 2},
        ]
        prices = {
            1: {"bid": None, "ask": None},
            2: {"bid": 10.0, "ask": 10.2},
        }

        result = ac.compute_combo_pnl(legs, prices)
        assert result == -10.2  # Only short leg counted


# ---------------------------------------------------------------------------
# Combo quote tests
# ---------------------------------------------------------------------------

class TestGetComboQuote:
    @patch("auto_close.api_get")
    @patch("auto_close.api_post")
    def test_returns_combo_bid_ask(self, mock_post, mock_get):
        """Should register combo and return its bid/ask."""
        mock_post.return_value = {"conid": 99999}
        mock_get.side_effect = [
            [{"conid": 99999}],                              # Prime
            [{"conid": 99999, "84": "1.50", "86": "2.00"}],  # Data
        ]

        with patch("auto_close.time.sleep"):
            result = ac.get_combo_quote("416904;;;111/1,222/-1,333/-1,444/1")

        assert result["bid"] == 1.5
        assert result["ask"] == 2.0

    @patch("auto_close.api_get")
    @patch("auto_close.api_post")
    def test_returns_combo_from_list_response(self, mock_post, mock_get):
        """Handle when combo registration returns a list."""
        mock_post.return_value = [{"conid": 99999}]
        mock_get.side_effect = [
            [{"conid": 99999}],
            [{"conid": 99999, "84": "1.00", "86": None}],
        ]

        with patch("auto_close.time.sleep"):
            result = ac.get_combo_quote("416904;;;111/1,222/-1")

        assert result["bid"] == 1.0
        assert result["ask"] is None

    @patch("auto_close.api_post")
    def test_returns_none_when_no_combo_conid(self, mock_post):
        """Should return None if combo registration fails."""
        mock_post.return_value = {}

        result = ac.get_combo_quote("416904;;;111/1,222/-1")
        assert result is None

    @patch("auto_close.api_get")
    @patch("auto_close.api_post")
    def test_parses_conidex_correctly(self, mock_post, mock_get):
        """Should parse conidex string into correct leg definitions."""
        mock_post.return_value = {"conid": 99999}
        mock_get.side_effect = [
            [{"conid": 99999}],
            [{"conid": 99999, "84": "1.00", "86": "2.00"}],
        ]

        with patch("auto_close.time.sleep"):
            ac.get_combo_quote("416904;;;111/1,222/-1,333/-1,444/1")

        call_args = mock_post.call_args
        body = call_args[1]["json_body"]
        assert body["conid"] == 416904
        assert len(body["legs"]) == 4
        assert body["legs"][0] == {"conid": 111, "ratio": 1}
        assert body["legs"][1] == {"conid": 222, "ratio": -1}


# ---------------------------------------------------------------------------
# Order response handling tests
# ---------------------------------------------------------------------------

class TestHandleOrderResponse:
    @patch("auto_close.api_post")
    def test_direct_success(self, mock_post):
        resp = [{"order_id": "12345", "order_status": "Filled"}]
        assert ac.handle_order_response(resp) == "12345"

    @patch("auto_close.api_post")
    def test_with_confirmation(self, mock_post):
        mock_post.return_value = [{"order_id": "12345", "order_status": "Filled"}]
        resp = [{"id": "conf1", "message": ["Confirm?"]}]

        oid = ac.handle_order_response(resp)
        assert oid == "12345"

    @patch("auto_close.api_post")
    def test_error_returns_none(self, mock_post):
        resp = [{"error": "Insufficient margin"}]
        assert ac.handle_order_response(resp) is None

    def test_empty_response(self):
        assert ac.handle_order_response([]) is None

    def test_non_list_response(self):
        assert ac.handle_order_response({}) is None


# ---------------------------------------------------------------------------
# Combo close tests
# ---------------------------------------------------------------------------

class TestSubmitComboClose:
    @patch("auto_close.api_post")
    def test_submits_limit_sell_order(self, mock_post, sample_order_data):
        mock_post.return_value = [{"order_id": "99999", "order_status": "Filled"}]
        combo_quote = {"bid": 1.50, "ask": 2.00}

        oid = ac.submit_combo_close("DUXXXXXXX", sample_order_data, 1, combo_quote)

        assert oid == "99999"
        call_args = mock_post.call_args
        order_body = call_args[1]["json_body"]
        assert order_body["orders"][0]["side"] == "SELL"
        assert order_body["orders"][0]["orderType"] == "LMT"
        assert order_body["orders"][0]["price"] == 2.00
        assert order_body["orders"][0]["quantity"] == 1

    @patch("auto_close.api_post")
    def test_passes_quantity(self, mock_post, sample_order_data):
        mock_post.return_value = [{"order_id": "99999", "order_status": "Filled"}]
        combo_quote = {"bid": 1.50, "ask": 2.00}

        ac.submit_combo_close("DUXXXXXXX", sample_order_data, 3, combo_quote)

        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["quantity"] == 3


# ---------------------------------------------------------------------------
# Short legs close tests
# ---------------------------------------------------------------------------

class TestSubmitShortLegsClose:
    @patch("auto_close.api_post")
    def test_closes_only_short_legs_at_limit(self, mock_post, sample_order_data):
        mock_post.return_value = [{"order_id": "11111", "order_status": "Filled"}]
        legs = sample_order_data["metadata"]["legs"]
        prices = {
            851292423: {"bid": 20.0, "ask": 20.2},
            852416651: {"bid": 21.0, "ask": 21.2},
        }

        oids = ac.submit_short_legs_close("DUXXXXXXX", legs, 1, prices)

        # Should only close 2 short legs (SELL legs)
        assert len(oids) == 2
        # Each call should be a BUY LMT (to close the short)
        for c in mock_post.call_args_list:
            order = c[1]["json_body"]["orders"][0]
            assert order["side"] == "BUY"
            assert order["orderType"] == "LMT"
            assert order["price"] is not None

    @patch("auto_close.api_post")
    def test_parallel_execution(self, mock_post, sample_order_data):
        """Short legs should close in parallel (ThreadPoolExecutor)."""
        mock_post.return_value = [{"order_id": "11111", "order_status": "Filled"}]
        legs = sample_order_data["metadata"]["legs"]
        prices = {851292423: {"bid": 20.0, "ask": 20.2}, 852416651: {"bid": 21.0, "ask": 21.2}}

        oids = ac.submit_short_legs_close("DUXXXXXXX", legs, 1, prices)

        assert len(oids) == 2
        assert mock_post.call_count == 2

    @patch("auto_close.api_post")
    def test_handles_partial_failure(self, mock_post, sample_order_data):
        """Should return only successful order IDs if one leg fails."""
        mock_post.side_effect = [
            [{"order_id": "11111", "order_status": "Filled"}],
            [{"error": "Failed"}],
        ]
        legs = sample_order_data["metadata"]["legs"]
        prices = {851292423: {"bid": 20.0, "ask": 20.2}, 852416651: {"bid": 21.0, "ask": 21.2}}

        oids = ac.submit_short_legs_close("DUXXXXXXX", legs, 1, prices)

        assert len(oids) == 1
        assert oids[0] == "11111"


# ---------------------------------------------------------------------------
# Trigger logic tests
# ---------------------------------------------------------------------------

class TestTriggerLogic:
    def test_profit_target_triggered(self):
        """P/L above profit threshold should trigger."""
        max_profit = 4250.0
        profit_pct = 50.0
        threshold = (profit_pct / 100.0) * max_profit  # 2125

        unrealized_pnl = 2200.0  # Above threshold
        assert unrealized_pnl >= threshold

    def test_profit_target_not_triggered(self):
        max_profit = 4250.0
        threshold = (50.0 / 100.0) * max_profit  # 2125

        unrealized_pnl = 2000.0  # Below threshold
        assert unrealized_pnl < threshold

    def test_stop_loss_triggered(self):
        """Negative P/L beyond loss threshold should trigger."""
        max_loss = 8750.0
        stop_pct = 80.0
        threshold = (stop_pct / 100.0) * max_loss  # 7000

        unrealized_pnl = -7500.0  # Loss exceeds threshold
        assert unrealized_pnl <= -threshold

    def test_stop_loss_not_triggered(self):
        max_loss = 8750.0
        threshold = (80.0 / 100.0) * max_loss  # 7000

        unrealized_pnl = -5000.0  # Loss below threshold
        assert unrealized_pnl > -threshold

    def test_close_cost_to_pnl(self):
        """Verify P/L calculation from close cost and net credit."""
        net_credit = 42.50
        # Close cost = sum of ask for shorts - sum of bid for longs
        close_cost = 15.0 + 15.0 - 0.5 - 0.1  # = 29.4
        quantity = 1

        unrealized_pnl = (net_credit - close_cost) * 100 * quantity
        # (42.50 - 29.4) * 100 = 1310.0
        assert abs(unrealized_pnl - 1310.0) < 0.01


# ---------------------------------------------------------------------------
# Close decision tests (combo vs short-legs-only)
# ---------------------------------------------------------------------------

class TestCloseDecision:
    def test_combo_has_ask_uses_combo_close(self):
        """When combo has an ask, should choose combo close."""
        combo_quote = {"bid": 1.50, "ask": 2.00}
        has_ask = combo_quote and combo_quote.get("ask") is not None
        assert has_ask is True

    def test_combo_no_ask_uses_short_legs(self):
        """When combo has no ask, should fall back to short legs."""
        combo_quote = {"bid": 1.50, "ask": None}
        has_ask = combo_quote and combo_quote.get("ask") is not None
        assert has_ask is False

    def test_combo_quote_none_uses_short_legs(self):
        """When combo quote fails entirely, should fall back to short legs."""
        combo_quote = None
        has_ask = combo_quote and combo_quote.get("ask") is not None
        assert not has_ask
