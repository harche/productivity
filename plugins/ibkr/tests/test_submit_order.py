"""Tests for submit_order.py — order submission and dry run."""

from unittest.mock import patch, MagicMock

import pytest

import submit_order as so


class TestLoadFromFile:
    def test_loads_valid_json(self, order_file: str, sample_order_data: dict) -> None:
        result = so.load_from_file(order_file)
        assert result["account_id"] == sample_order_data["account_id"]

    def test_raises_on_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            so.load_from_file("/nonexistent/file.json")


class TestBuildFromArgs:
    def test_single_contract(self) -> None:
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
        assert result["orders"][0]["conid"] == 265598
        assert result["orders"][0]["price"] == 150.0

    def test_combo_order(self) -> None:
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

    def test_outside_rth_flag(self) -> None:
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


class TestFetchLivePrices:
    @patch("ibkr_client.api_get")
    def test_fetches_and_displays_prices(self, mock_get: MagicMock, sample_order_data: dict, capsys) -> None:
        import time as _time
        now_ms = int(_time.time() * 1000)
        mock_get.side_effect = [
            [{"conid": 859216550}, {"conid": 851292423}, {"conid": 852416651}, {"conid": 852416755}],
            [
                {"conid": 859216550, "84": "1.20", "86": "1.30", "31": "1.25", "_updated": now_ms},
                {"conid": 851292423, "84": "20.00", "86": "20.20", "31": "20.10", "_updated": now_ms},
                {"conid": 852416651, "84": "23.00", "86": "23.20", "31": "23.10", "_updated": now_ms},
                {"conid": 852416755, "84": "0.10", "86": "0.15", "31": "0.12", "_updated": now_ms},
            ],
        ]

        with patch("ibkr_client.time.sleep"):
            so.fetch_live_prices(sample_order_data)

        output = capsys.readouterr().out
        assert "LIVE PRICES" in output

    def test_no_legs_skips(self, capsys) -> None:
        so.fetch_live_prices({"metadata": {}})
        assert capsys.readouterr().out == ""

    @patch("ibkr_client.api_get")
    def test_handles_api_error(self, mock_get: MagicMock, sample_order_data: dict, capsys) -> None:
        mock_get.side_effect = Exception("Connection refused")

        so.fetch_live_prices(sample_order_data)
        assert "Could not fetch live prices" in capsys.readouterr().out
