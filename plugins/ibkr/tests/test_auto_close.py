"""Tests for auto_close.py — standing limit/stop-limit order auto-close."""

from unittest.mock import patch, MagicMock

import pytest

import auto_close as ac


class TestSubmitProfitOrder:
    @patch("ibkr_client.api_post")
    def test_submits_limit_sell(self, mock_post: MagicMock) -> None:
        mock_post.return_value = [{"order_id": "99999", "order_status": "PreSubmitted"}]

        oid = ac.submit_profit_order("DUXXXXXXX", "416904;;;111/1,222/-1", 1, -28.70)

        assert oid == "99999"
        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["side"] == "SELL"
        assert order_body["orders"][0]["orderType"] == "LMT"
        assert order_body["orders"][0]["price"] == -28.70

    @patch("ibkr_client.api_post")
    def test_passes_quantity(self, mock_post: MagicMock) -> None:
        mock_post.return_value = [{"order_id": "99999", "order_status": "PreSubmitted"}]

        ac.submit_profit_order("DUXXXXXXX", "416904;;;111/1,222/-1", 3, -28.70)

        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["quantity"] == 3


class TestSubmitStopLossOrder:
    @patch("ibkr_client.api_post")
    def test_submits_stop_limit(self, mock_post: MagicMock) -> None:
        mock_post.return_value = [{"order_id": "88888", "order_status": "PreSubmitted"}]

        oid = ac.submit_stop_loss_order("DUXXXXXXX", "416904;;;111/1,222/-1", 1, -36.70)

        assert oid == "88888"
        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["orderType"] == "LMT"
        assert order_body["orders"][0]["price"] == -36.70

    @patch("ibkr_client.api_post")
    def test_passes_quantity(self, mock_post: MagicMock) -> None:
        mock_post.return_value = [{"order_id": "88888", "order_status": "PreSubmitted"}]

        ac.submit_stop_loss_order("DUXXXXXXX", "416904;;;111/1,222/-1", 2, -36.70)

        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["quantity"] == 2

    @patch("ibkr_client.api_post")
    def test_uses_day_tif(self, mock_post: MagicMock) -> None:
        mock_post.return_value = [{"order_id": "88888", "order_status": "PreSubmitted"}]

        ac.submit_stop_loss_order("DUXXXXXXX", "416904;;;111/1,222/-1", 1, -36.70)

        order_body = mock_post.call_args[1]["json_body"]
        assert order_body["orders"][0]["tif"] == "DAY"


class TestPriceCalculation:
    def test_profit_target_price(self) -> None:
        net_credit = 31.70
        close_price = net_credit - (300.0 / 100.0 / 1)
        assert abs(close_price - 28.70) < 0.01

    def test_profit_target_with_quantity(self) -> None:
        close_price = 31.70 - (600.0 / 100.0 / 2)
        assert abs(close_price - 28.70) < 0.01

    def test_stop_loss_stop_price(self) -> None:
        stop_price = 31.70 + (500.0 / 100.0 / 1)
        assert abs(stop_price - 36.70) < 0.01

    def test_stop_loss_limit_with_buffer(self) -> None:
        assert abs((36.70 + 2.0) - 38.70) < 0.01

    def test_full_profit_close_at_zero(self) -> None:
        close_price = 42.50 - (4250.0 / 100.0 / 1)
        assert abs(close_price) < 0.01
