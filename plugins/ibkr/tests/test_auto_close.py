"""Tests for auto_close.py — standing limit/stop-limit order auto-close."""

import json
from unittest.mock import patch, MagicMock

import pytest

import auto_close as ac


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
# Profit order submission tests
# ---------------------------------------------------------------------------

class TestSubmitProfitOrder:
    @patch("auto_close.api_post")
    def test_submits_limit_sell(self, mock_post):
        mock_post.return_value = [{"order_id": "99999", "order_status": "PreSubmitted"}]

        oid = ac.submit_profit_order("DUXXXXXXX", "416904;;;111/1,222/-1", 1, -28.70)

        assert oid == "99999"
        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["side"] == "SELL"
        assert order_body["orders"][0]["orderType"] == "LMT"
        assert order_body["orders"][0]["price"] == -28.70
        assert order_body["orders"][0]["quantity"] == 1
        assert "auxPrice" not in order_body["orders"][0]

    @patch("auto_close.api_post")
    def test_passes_quantity(self, mock_post):
        mock_post.return_value = [{"order_id": "99999", "order_status": "PreSubmitted"}]

        ac.submit_profit_order("DUXXXXXXX", "416904;;;111/1,222/-1", 3, -28.70)

        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["quantity"] == 3


# ---------------------------------------------------------------------------
# Stop-loss order submission tests
# ---------------------------------------------------------------------------

class TestSubmitStopLossOrder:
    @patch("auto_close.api_post")
    def test_submits_stop_limit(self, mock_post):
        mock_post.return_value = [{"order_id": "88888", "order_status": "PreSubmitted"}]

        oid = ac.submit_stop_loss_order("DUXXXXXXX", "416904;;;111/1,222/-1", 1, -36.70, -38.70)

        assert oid == "88888"
        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["side"] == "SELL"
        assert order_body["orders"][0]["orderType"] == "STP_LIMIT"
        assert order_body["orders"][0]["auxPrice"] == -36.70  # stop trigger
        assert order_body["orders"][0]["price"] == -38.70     # limit fill
        assert order_body["orders"][0]["quantity"] == 1

    @patch("auto_close.api_post")
    def test_passes_quantity(self, mock_post):
        mock_post.return_value = [{"order_id": "88888", "order_status": "PreSubmitted"}]

        ac.submit_stop_loss_order("DUXXXXXXX", "416904;;;111/1,222/-1", 2, -36.70, -38.70)

        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["quantity"] == 2

    @patch("auto_close.api_post")
    def test_uses_day_tif(self, mock_post):
        mock_post.return_value = [{"order_id": "88888", "order_status": "PreSubmitted"}]

        ac.submit_stop_loss_order("DUXXXXXXX", "416904;;;111/1,222/-1", 1, -36.70, -38.70)

        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["tif"] == "DAY"


# ---------------------------------------------------------------------------
# Price calculation tests
# ---------------------------------------------------------------------------

class TestPriceCalculation:
    def test_profit_target_price(self):
        """Profit of $300 on net_credit 31.70 -> close at 28.70."""
        net_credit = 31.70
        profit = 300.0
        quantity = 1
        close_price = net_credit - (profit / 100.0 / quantity)
        assert abs(close_price - 28.70) < 0.01

    def test_profit_target_with_quantity(self):
        """Profit of $600 on 2 contracts, net_credit 31.70 -> close at 28.70."""
        net_credit = 31.70
        profit = 600.0
        quantity = 2
        close_price = net_credit - (profit / 100.0 / quantity)
        assert abs(close_price - 28.70) < 0.01

    def test_stop_loss_stop_price(self):
        """Stop loss of $500 on net_credit 31.70 -> stop at 36.70."""
        net_credit = 31.70
        stop_loss = 500.0
        quantity = 1
        stop_price = net_credit + (stop_loss / 100.0 / quantity)
        assert abs(stop_price - 36.70) < 0.01

    def test_stop_loss_limit_with_buffer(self):
        """Stop at 36.70 + 2.0 buffer -> limit at 38.70."""
        stop_price = 36.70
        buffer = 2.0
        limit_price = stop_price + buffer
        assert abs(limit_price - 38.70) < 0.01

    def test_stop_loss_custom_buffer(self):
        """Stop at 36.70 + 3.0 buffer -> limit at 39.70."""
        stop_price = 36.70
        buffer = 3.0
        limit_price = stop_price + buffer
        assert abs(limit_price - 39.70) < 0.01

    def test_stop_loss_with_quantity(self):
        """Stop loss of $1000 on 2 contracts, net_credit 31.70 -> stop at 36.70."""
        net_credit = 31.70
        stop_loss = 1000.0
        quantity = 2
        stop_price = net_credit + (stop_loss / 100.0 / quantity)
        assert abs(stop_price - 36.70) < 0.01

    def test_full_profit_close_at_zero(self):
        """Full max profit -> close at 0."""
        net_credit = 42.50
        profit = 4250.0
        quantity = 1
        close_price = net_credit - (profit / 100.0 / quantity)
        assert abs(close_price - 0.0) < 0.01


# ---------------------------------------------------------------------------
# Session tests
# ---------------------------------------------------------------------------

class TestInitializeSession:
    @patch("auto_close.api_get")
    def test_authenticated(self, mock_get):
        mock_get.side_effect = [
            {"accounts": ["DUXXXXXXX"]},
            {"authenticated": True, "connected": True},
        ]
        ac.initialize_session()

    @patch("auto_close.api_get")
    def test_not_authenticated_exits(self, mock_get):
        mock_get.side_effect = [
            {"accounts": ["DUXXXXXXX"]},
            {"authenticated": False, "connected": True},
        ]
        with pytest.raises(SystemExit):
            ac.initialize_session()


# ---------------------------------------------------------------------------
# API retry tests
# ---------------------------------------------------------------------------

class TestApiRetry:
    @patch("auto_close.requests.get")
    def test_retries_on_500(self, mock_get):
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"ok": True}
        ok_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [fail_resp, ok_resp]

        with patch("auto_close.time.sleep"):
            result = ac.api_get("/test")

        assert result == {"ok": True}
        assert mock_get.call_count == 2

    @patch("auto_close.requests.post")
    def test_post_retries_on_500(self, mock_post):
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"order_id": "123"}
        ok_resp.raise_for_status = MagicMock()

        mock_post.side_effect = [fail_resp, ok_resp]

        with patch("auto_close.time.sleep"):
            result = ac.api_post("/test")

        assert result == {"order_id": "123"}
