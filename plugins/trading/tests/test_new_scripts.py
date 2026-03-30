"""Tests for cancel_order.py, modify_order.py, and account_summary.py."""

from unittest.mock import patch, MagicMock

import pytest

import cancel_order as co
import modify_order as mo
import account_summary as acc


# ---------------------------------------------------------------------------
# cancel_order.py tests
# ---------------------------------------------------------------------------

class TestCancelSingleOrder:
    @patch("cancel_order.cancel_order")
    def test_success(self, mock_cancel: MagicMock) -> None:
        mock_cancel.return_value = {"msg": "Order 12345 cancelled"}
        assert co.cancel_single_order("DUXXXXXXX", "12345") is True

    @patch("cancel_order.cancel_order")
    def test_failure(self, mock_cancel: MagicMock) -> None:
        mock_cancel.side_effect = Exception("Not found")
        assert co.cancel_single_order("DUXXXXXXX", "99999") is False


class TestCancelAllOpenOrders:
    @patch("cancel_order.cancel_order")
    @patch("cancel_order.get_live_orders")
    def test_cancels_non_filled(self, mock_orders: MagicMock, mock_cancel: MagicMock, capsys) -> None:
        mock_orders.return_value = [
            {"orderId": 111, "status": "PreSubmitted", "ticker": "SPX", "side": "SELL",
             "remainingQuantity": 1, "price": "-28.70"},
            {"orderId": 222, "status": "Filled", "ticker": "SPX", "side": "BUY",
             "remainingQuantity": 0, "price": "-31.70"},
        ]
        mock_cancel.return_value = {"msg": "Cancelled"}

        co.cancel_all_open_orders("DUXXXXXXX")

        # Should only cancel the PreSubmitted order, not the Filled one
        mock_cancel.assert_called_once_with("DUXXXXXXX", "111")

    @patch("cancel_order.get_live_orders")
    def test_no_open_orders(self, mock_orders: MagicMock, capsys) -> None:
        mock_orders.return_value = [
            {"orderId": 111, "status": "Filled"},
        ]
        co.cancel_all_open_orders("DUXXXXXXX")
        assert "No open orders" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# modify_order.py tests
# ---------------------------------------------------------------------------

class TestDisplayOrderDetails:
    def test_displays_fields(self, capsys) -> None:
        details = {
            "orderId": "12345", "ticker": "SPX", "side": "SELL",
            "orderType": "Limit", "totalSize": 1, "price": "-28.70",
            "status": "PreSubmitted",
        }
        mo.display_order_details("TEST ORDER", details)
        output = capsys.readouterr().out
        assert "TEST ORDER" in output
        assert "12345" in output
        assert "SPX" in output


# ---------------------------------------------------------------------------
# account_summary.py tests
# ---------------------------------------------------------------------------

class TestExtractValue:
    def test_flat_value(self) -> None:
        summary = {"netliquidation": 50000.0}
        assert acc.extract_value(summary, "netliquidation") == 50000.0

    def test_nested_value(self) -> None:
        summary = {"netliquidation": {"amount": 50000.0, "currency": "USD"}}
        assert acc.extract_value(summary, "netliquidation") == 50000.0

    def test_missing_key(self) -> None:
        assert acc.extract_value({}, "netliquidation") is None


class TestFormatValue:
    def test_currency(self) -> None:
        result = acc.format_value(50000.0, "currency")
        assert "$" in result
        assert "50,000.00" in result

    def test_percent(self) -> None:
        result = acc.format_value(0.25, "percent")
        assert "25.00%" in result

    def test_integer(self) -> None:
        result = acc.format_value(3.0, "integer")
        assert "3" in result

    def test_none(self) -> None:
        assert acc.format_value(None, "currency") == "N/A"


class TestDisplaySummary:
    def test_displays_metrics(self, capsys) -> None:
        summary = {
            "netliquidation": {"amount": 100000.0, "currency": "USD"},
            "buyingpower": 200000.0,
            "availablefunds": 80000.0,
            "cushion": 0.35,
        }
        acc.display_summary(summary)
        output = capsys.readouterr().out
        assert "ACCOUNT SUMMARY" in output
        assert "100,000.00" in output
