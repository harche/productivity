"""Tests for monitor.py — position monitoring."""

from unittest.mock import patch, MagicMock

import pytest

import monitor as mon


class TestFormatCurrency:
    def test_positive(self) -> None:
        assert mon.format_currency(1234.56) == "$1,234.56"

    def test_negative(self) -> None:
        assert mon.format_currency(-500.0) == "$-500.00"

    def test_none(self) -> None:
        assert mon.format_currency(None) == "N/A"


class TestFormatPnl:
    def test_positive(self) -> None:
        assert mon.format_pnl(500.0) == "+$500.00"

    def test_negative(self) -> None:
        assert mon.format_pnl(-300.0) == "$-300.00"

    def test_none(self) -> None:
        assert mon.format_pnl(None) == "N/A"


class TestFormatPct:
    def test_positive(self) -> None:
        assert mon.format_pct(25.5) == "+25.50%"

    def test_negative(self) -> None:
        assert mon.format_pct(-10.3) == "-10.30%"

    def test_none(self) -> None:
        assert mon.format_pct(None) == "N/A"


class TestFetchAllPositions:
    @patch("monitor.get_positions")
    def test_single_page(self, mock_get: MagicMock) -> None:
        mock_get.return_value = [
            {"ticker": "SPX", "position": -1, "assetClass": "OPT"},
            {"ticker": "AAPL", "position": 100, "assetClass": "STK"},
        ]
        result = mon._fetch_all_positions("DUXXXXXXX")
        assert len(result) == 2

    @patch("monitor.get_positions")
    def test_symbol_filter(self, mock_get: MagicMock) -> None:
        mock_get.return_value = [
            {"ticker": "SPX OPT", "contractDesc": "SPX MAR2026", "position": -1},
            {"ticker": "AAPL STK", "contractDesc": "AAPL", "position": 100},
        ]
        result = mon._fetch_all_positions("DUXXXXXXX", symbol_filter="SPX")
        assert len(result) == 1

    @patch("monitor.get_positions")
    def test_symbol_filter_case_insensitive(self, mock_get: MagicMock) -> None:
        mock_get.return_value = [
            {"ticker": "AAPL STK", "contractDesc": "AAPL", "position": 100},
        ]
        result = mon._fetch_all_positions("DUXXXXXXX", symbol_filter="aapl")
        assert len(result) == 1


class TestDisplayPositions:
    def test_displays_positions(self, capsys) -> None:
        positions = [
            {
                "ticker": "SPX", "contractDesc": "SPX MAR2026 6780 C",
                "position": -1, "mktPrice": 27.10, "mktValue": -2710.0,
                "unrealizedPnl": -501.64, "avgCost": 22.10, "assetClass": "OPT",
            },
        ]
        mon.display_positions(positions, "DUXXXXXXX")
        output = capsys.readouterr().out
        assert "OPTIONS" in output

    def test_empty_positions(self, capsys) -> None:
        mon.display_positions([], "DUXXXXXXX")
        assert "No open positions" in capsys.readouterr().out

    def test_groups_by_asset_class(self, capsys) -> None:
        positions = [
            {"ticker": "AAPL", "contractDesc": "AAPL", "position": 100,
             "mktPrice": 150.0, "mktValue": 15000.0, "unrealizedPnl": 500.0,
             "avgCost": 145.0, "assetClass": "STK"},
            {"ticker": "SPX", "contractDesc": "SPX Call", "position": -1,
             "mktPrice": 20.0, "mktValue": -2000.0, "unrealizedPnl": -100.0,
             "avgCost": 19.0, "assetClass": "OPT"},
        ]
        mon.display_positions(positions, "DUXXXXXXX")
        output = capsys.readouterr().out
        assert "OPTIONS" in output
        assert "STOCKS" in output

    def test_total_calculation(self, capsys) -> None:
        positions = [
            {"ticker": "A", "contractDesc": "A", "position": 1,
             "mktPrice": 10.0, "mktValue": 1000.0, "unrealizedPnl": 100.0,
             "avgCost": 9.0, "assetClass": "STK"},
            {"ticker": "B", "contractDesc": "B", "position": 1,
             "mktPrice": 20.0, "mktValue": 2000.0, "unrealizedPnl": -50.0,
             "avgCost": 20.5, "assetClass": "STK"},
        ]
        mon.display_positions(positions, "DUXXXXXXX")
        output = capsys.readouterr().out
        assert "$3,000.00" in output
        assert "+$50.00" in output

    def test_greeks_mode(self, capsys) -> None:
        positions = [
            {"ticker": "SPX", "contractDesc": "SPX Call", "position": -1,
             "mktPrice": 20.0, "mktValue": -2000.0, "unrealizedPnl": -100.0,
             "avgCost": 19.0, "assetClass": "OPT", "conid": 12345},
        ]
        greeks = {12345: {"delta": 0.45, "gamma": 0.02, "theta": -1.5, "vega": 0.3, "iv": "25.0%"}}
        mon.display_positions(positions, "DUXXXXXXX", greeks=greeks)
        output = capsys.readouterr().out
        assert "Delta" in output
        assert "0.450" in output
