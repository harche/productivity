"""Tests for submit_order.py — order submission and dry run."""

import json
from unittest.mock import patch, MagicMock

import pytest

import submit_order as so


# ---------------------------------------------------------------------------
# Order loading tests
# ---------------------------------------------------------------------------

class TestLoadFromFile:
    def test_loads_valid_json(self, order_file, sample_order_data):
        result = so.load_from_file(order_file)
        assert result["account_id"] == sample_order_data["account_id"]
        assert len(result["orders"]) == 1

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            so.load_from_file("/nonexistent/file.json")


# ---------------------------------------------------------------------------
# CLI argument building tests
# ---------------------------------------------------------------------------

class TestBuildFromArgs:
    def test_single_contract(self):
        args = MagicMock()
        args.account = "DUXXXXXXX"
        args.conid = 265598
        args.conidex = None
        args.side = "BUY"
        args.quantity = 10
        args.order_type = "LMT"
        args.price = 150.0
        args.aux_price = None
        args.tif = "DAY"
        args.outside_rth = False

        result = so.build_from_args(args)
        assert result["account_id"] == "DUXXXXXXX"
        assert result["orders"][0]["conid"] == 265598
        assert result["orders"][0]["side"] == "BUY"
        assert result["orders"][0]["price"] == 150.0

    def test_combo_order(self):
        args = MagicMock()
        args.account = "DUXXXXXXX"
        args.conid = None
        args.conidex = "416904;;;111/1,222/-1"
        args.side = "BUY"
        args.quantity = 1
        args.order_type = "LMT"
        args.price = -35.0
        args.aux_price = None
        args.tif = "DAY"
        args.outside_rth = False

        result = so.build_from_args(args)
        assert result["orders"][0]["conidex"] == "416904;;;111/1,222/-1"
        assert "conid" not in result["orders"][0]

    def test_outside_rth_flag(self):
        args = MagicMock()
        args.account = "DUXXXXXXX"
        args.conid = 265598
        args.conidex = None
        args.side = "BUY"
        args.quantity = 1
        args.order_type = "LMT"
        args.price = 150.0
        args.aux_price = None
        args.tif = "DAY"
        args.outside_rth = True

        result = so.build_from_args(args)
        assert result["orders"][0]["outsideRTH"] is True


# ---------------------------------------------------------------------------
# API retry tests
# ---------------------------------------------------------------------------

class TestApiRetry:
    @patch("submit_order.requests.get")
    def test_retries_on_500(self, mock_get):
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"ok": True}
        ok_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [fail_resp, ok_resp]

        with patch("submit_order.time.sleep"):
            result = so.api_get("/test")

        assert result == {"ok": True}
        assert mock_get.call_count == 2

    @patch("submit_order.requests.post")
    def test_post_retries_on_500(self, mock_post):
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"order_id": "123"}
        ok_resp.raise_for_status = MagicMock()

        mock_post.side_effect = [fail_resp, ok_resp]

        with patch("submit_order.time.sleep"):
            result = so.api_post("/test")

        assert result == {"order_id": "123"}


# ---------------------------------------------------------------------------
# Order submission / confirmation chain tests
# ---------------------------------------------------------------------------

class TestSubmitOrder:
    @patch("submit_order.api_post")
    def test_direct_success(self, mock_post):
        """Order accepted without confirmation prompts."""
        mock_post.return_value = [{"order_id": "12345", "order_status": "Filled"}]
        order_data = {"account_id": "DUXXXXXXX", "orders": [{"conid": 1, "side": "BUY", "quantity": 1}]}

        oid = so.submit_order(order_data)
        assert oid == "12345"

    @patch("submit_order.api_post")
    def test_single_confirmation(self, mock_post):
        """Order requires one confirmation prompt."""
        mock_post.side_effect = [
            [{"id": "conf1", "message": ["Are you sure?"]}],
            [{"order_id": "12345", "order_status": "PreSubmitted"}],
        ]
        order_data = {"account_id": "DUXXXXXXX", "orders": [{"conid": 1, "side": "BUY", "quantity": 1}]}

        oid = so.submit_order(order_data)
        assert oid == "12345"
        assert mock_post.call_count == 2

    @patch("submit_order.api_post")
    def test_multiple_confirmations(self, mock_post):
        """Order requires multiple confirmation prompts."""
        mock_post.side_effect = [
            [{"id": "conf1", "message": ["Price exceeds limit"]}],
            [{"id": "conf2", "message": ["Confirm order?"]}],
            [{"order_id": "12345", "order_status": "Filled"}],
        ]
        order_data = {"account_id": "DUXXXXXXX", "orders": [{"conid": 1, "side": "BUY", "quantity": 1}]}

        oid = so.submit_order(order_data)
        assert oid == "12345"
        assert mock_post.call_count == 3

    @patch("submit_order.api_post")
    def test_error_response(self, mock_post):
        """Order returns an error."""
        mock_post.return_value = [{"error": "Insufficient funds"}]
        order_data = {"account_id": "DUXXXXXXX", "orders": [{"conid": 1, "side": "BUY", "quantity": 1}]}

        oid = so.submit_order(order_data)
        assert oid is None

    @patch("submit_order.api_post")
    def test_empty_response(self, mock_post):
        """Order returns empty response."""
        mock_post.return_value = []
        order_data = {"account_id": "DUXXXXXXX", "orders": [{"conid": 1, "side": "BUY", "quantity": 1}]}

        oid = so.submit_order(order_data)
        assert oid is None


# ---------------------------------------------------------------------------
# Parse price tests
# ---------------------------------------------------------------------------

class TestParsePrice:
    def test_none(self):
        assert so.parse_price(None) is None

    def test_float(self):
        assert so.parse_price(42.5) == 42.5

    def test_string_with_prefix(self):
        assert so.parse_price("C21.40") == 21.4

    def test_invalid(self):
        assert so.parse_price("N/A") is None


# ---------------------------------------------------------------------------
# Live price comparison tests (dry run)
# ---------------------------------------------------------------------------

class TestFetchLivePrices:
    @patch("submit_order.api_get")
    def test_fetches_and_displays_prices(self, mock_get, sample_order_data, capsys):
        """Dry run should fetch live prices for all legs."""
        mock_get.side_effect = [
            # Prime call
            [{"conid": 859216550}, {"conid": 851292423}, {"conid": 852416651}, {"conid": 852416755}],
            # Data call
            [
                {"conid": 859216550, "84": "1.20", "86": "1.30", "31": "1.25"},
                {"conid": 851292423, "84": "20.00", "86": "20.20", "31": "20.10"},
                {"conid": 852416651, "84": "23.00", "86": "23.20", "31": "23.10"},
                {"conid": 852416755, "84": "0.10", "86": "0.15", "31": "0.12"},
            ],
        ]

        with patch("submit_order.time.sleep"):
            so.fetch_live_prices(sample_order_data)

        output = capsys.readouterr().out
        assert "LIVE PRICES" in output
        assert "Long Put (wing)" in output
        assert "Short Put (ATM)" in output

    def test_no_legs_skips(self, capsys):
        """Should do nothing if no legs in metadata."""
        so.fetch_live_prices({"metadata": {}})
        output = capsys.readouterr().out
        assert output == ""

    @patch("submit_order.api_get")
    def test_handles_api_error(self, mock_get, sample_order_data, capsys):
        """Should handle API errors gracefully."""
        mock_get.side_effect = Exception("Connection refused")

        so.fetch_live_prices(sample_order_data)
        output = capsys.readouterr().out
        assert "Could not fetch live prices" in output


# ---------------------------------------------------------------------------
# Session initialization tests
# ---------------------------------------------------------------------------

class TestInitializeSession:
    @patch("submit_order.api_get")
    def test_authenticated(self, mock_get, mock_accounts, mock_auth_status):
        mock_get.side_effect = [mock_accounts, mock_auth_status]

        with patch("submit_order.time.sleep"):
            so.initialize_session()  # Should not raise

    @patch("submit_order.api_get")
    def test_not_authenticated_exits(self, mock_get, mock_accounts):
        mock_get.side_effect = [mock_accounts, {"authenticated": False, "connected": True}]

        with patch("submit_order.time.sleep"):
            with pytest.raises(SystemExit):
                so.initialize_session()
