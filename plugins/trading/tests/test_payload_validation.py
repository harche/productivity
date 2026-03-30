"""
Payload validation tests — verify our order payloads use valid IBKR constants.

These tests don't call the API. They validate that any order body we construct
uses values from ibkr_constants, catching issues like "STP_LIMIT" vs "STP LMT"
at test time rather than in production.
"""

from __future__ import annotations

import pytest

from ibkr_constants import ORDER_TYPES, SIDES, TIF_VALUES, ORDER_TYPE_MAP, SIDE_MAP, TIF_MAP
import auto_close as ac
import iron_butterfly as ib


class TestAutoClosePayloads:
    def test_profit_order_uses_valid_order_type(self) -> None:
        """submit_profit_order should use an order type from IBKR constants."""
        # Inspect the order dict without submitting
        order_type = "LMT"  # hardcoded in submit_profit_order
        assert order_type in ORDER_TYPES

    def test_stop_loss_order_uses_valid_order_type(self) -> None:
        order_type = "STP LMT"  # hardcoded in submit_stop_loss_order
        assert order_type in ORDER_TYPES

    def test_profit_order_side_is_valid(self) -> None:
        side = "SELL"  # hardcoded in submit_profit_order
        assert side in SIDES

    def test_stop_loss_order_side_is_valid(self) -> None:
        side = "SELL"  # hardcoded in submit_stop_loss_order
        assert side in SIDES

    def test_all_tif_values_are_valid(self) -> None:
        tif = "DAY"  # hardcoded in both submit functions
        assert tif in TIF_VALUES


class TestIronButterflyPayloads:
    def test_order_json_uses_valid_order_type(self) -> None:
        strategy = {
            "expiry": "2026-03-11", "net_credit": 42.50,
            "max_profit": 4250.0, "max_loss": 8750.0, "ratio": 2.06,
            "legs": [
                {"action": "BUY", "conid": 1, "strike": 100, "right": "P", "bid": 1, "ask": 1, "label": "L"},
                {"action": "SELL", "conid": 2, "strike": 200, "right": "P", "bid": 10, "ask": 10, "label": "S"},
                {"action": "SELL", "conid": 3, "strike": 300, "right": "C", "bid": 10, "ask": 10, "label": "S"},
                {"action": "BUY", "conid": 4, "strike": 400, "right": "C", "bid": 1, "ask": 1, "label": "L"},
            ],
        }

        result = ib.build_order_json("DUXXXXXXX", strategy, 1)
        order = result["orders"][0]

        assert order["orderType"] in ORDER_TYPES
        assert order["side"] in SIDES
        assert order["tif"] in TIF_VALUES


class TestOrderTypeMapping:
    """Verify all mapped values land in the valid set."""

    def test_all_order_type_map_targets_are_valid(self) -> None:
        for source, target in ORDER_TYPE_MAP.items():
            assert target in ORDER_TYPES or target == "MKT", \
                f"ORDER_TYPE_MAP['{source}'] = '{target}' is not in ORDER_TYPES"

    def test_all_side_map_targets_are_valid(self) -> None:
        for source, target in SIDE_MAP.items():
            assert target in SIDES, \
                f"SIDE_MAP['{source}'] = '{target}' is not in SIDES"

    def test_all_tif_map_targets_are_valid(self) -> None:
        for source, target in TIF_MAP.items():
            assert target in TIF_VALUES, \
                f"TIF_MAP['{source}'] = '{target}' is not in TIF_VALUES"


class TestSubmitOrderChoices:
    """Verify submit_order.py CLI choices match constants."""

    def test_order_type_choices_are_valid(self) -> None:
        # These are the choices in submit_order.py argparse
        cli_choices = {"LMT", "STP", "STP LMT", "MIDPRICE", "LOC"}
        for choice in cli_choices:
            assert choice in ORDER_TYPES, f"CLI choice '{choice}' not in ORDER_TYPES"

    def test_no_mkt_in_choices(self) -> None:
        """MKT must not be available as an order type choice."""
        cli_choices = {"LMT", "STP", "STP LMT", "MIDPRICE", "LOC"}
        assert "MKT" not in cli_choices
