"""Tests for monitor.py — position monitoring."""

from unittest.mock import patch, MagicMock

import pytest

import monitor as mon


# ---------------------------------------------------------------------------
# Formatting tests
# ---------------------------------------------------------------------------

class TestFormatCurrency:
    def test_positive(self):
        assert mon.format_currency(1234.56) == "$1,234.56"

    def test_negative(self):
        assert mon.format_currency(-500.0) == "$-500.00"

    def test_zero(self):
        assert mon.format_currency(0) == "$0.00"

    def test_none(self):
        assert mon.format_currency(None) == "N/A"


class TestFormatPnl:
    def test_positive(self):
        assert mon.format_pnl(500.0) == "+$500.00"

    def test_negative(self):
        assert mon.format_pnl(-300.0) == "$-300.00"

    def test_zero(self):
        assert mon.format_pnl(0) == "+$0.00"

    def test_none(self):
        assert mon.format_pnl(None) == "N/A"


class TestFormatPct:
    def test_positive(self):
        assert mon.format_pct(25.5) == "+25.50%"

    def test_negative(self):
        assert mon.format_pct(-10.3) == "-10.30%"

    def test_none(self):
        assert mon.format_pct(None) == "N/A"


# ---------------------------------------------------------------------------
# Position fetching tests
# ---------------------------------------------------------------------------

class TestGetPositions:
    @patch("monitor.api_get")
    def test_single_page(self, mock_get):
        positions = [
            {"ticker": "SPX", "position": -1, "mktValue": -1000, "assetClass": "OPT"},
            {"ticker": "AAPL", "position": 100, "mktValue": 15000, "assetClass": "STK"},
        ]
        mock_get.return_value = positions

        with patch("monitor.time.sleep"):
            result = mon.get_positions("DUXXXXXXX")

        assert len(result) == 2

    @patch("monitor.api_get")
    def test_multi_page(self, mock_get):
        page0 = [{"ticker": f"SYM{i}", "position": 1} for i in range(30)]
        page1 = [{"ticker": "LAST", "position": 1}]

        mock_get.side_effect = [page0, page1]

        with patch("monitor.time.sleep"):
            result = mon.get_positions("DUXXXXXXX")

        assert len(result) == 31

    @patch("monitor.api_get")
    def test_empty_positions(self, mock_get):
        mock_get.return_value = []

        result = mon.get_positions("DUXXXXXXX")
        assert result == []

    @patch("monitor.api_get")
    def test_symbol_filter(self, mock_get):
        positions = [
            {"ticker": "SPX OPT", "contractDesc": "SPX MAR2026 6780 C", "position": -1},
            {"ticker": "AAPL STK", "contractDesc": "AAPL", "position": 100},
            {"ticker": "SPX OPT", "contractDesc": "SPX MAR2026 6775 P", "position": -1},
        ]
        mock_get.return_value = positions

        with patch("monitor.time.sleep"):
            result = mon.get_positions("DUXXXXXXX", symbol_filter="SPX")

        assert len(result) == 2

    @patch("monitor.api_get")
    def test_symbol_filter_case_insensitive(self, mock_get):
        positions = [
            {"ticker": "AAPL STK", "contractDesc": "AAPL", "position": 100},
        ]
        mock_get.return_value = positions

        with patch("monitor.time.sleep"):
            result = mon.get_positions("DUXXXXXXX", symbol_filter="aapl")

        assert len(result) == 1


# ---------------------------------------------------------------------------
# Display tests
# ---------------------------------------------------------------------------

class TestDisplayPositions:
    def test_displays_positions(self, capsys):
        positions = [
            {
                "ticker": "SPX", "contractDesc": "SPX MAR2026 6780 C",
                "position": -1, "mktPrice": 27.10, "mktValue": -2710.0,
                "unrealizedPnl": -501.64, "avgCost": 22.10, "assetClass": "OPT",
            },
        ]

        mon.display_positions(positions, "DUXXXXXXX")
        output = capsys.readouterr().out

        assert "DUXXXXXXX" in output
        assert "OPTIONS" in output
        assert "SPX MAR2026 6780 C" in output

    def test_empty_positions(self, capsys):
        mon.display_positions([], "DUXXXXXXX")
        output = capsys.readouterr().out
        assert "No open positions" in output

    def test_groups_by_asset_class(self, capsys):
        positions = [
            {"ticker": "AAPL", "contractDesc": "AAPL", "position": 100,
             "mktPrice": 150.0, "mktValue": 15000.0, "unrealizedPnl": 500.0,
             "avgCost": 145.0, "assetClass": "STK"},
            {"ticker": "SPX OPT", "contractDesc": "SPX Call", "position": -1,
             "mktPrice": 20.0, "mktValue": -2000.0, "unrealizedPnl": -100.0,
             "avgCost": 19.0, "assetClass": "OPT"},
        ]

        mon.display_positions(positions, "DUXXXXXXX")
        output = capsys.readouterr().out

        assert "OPTIONS" in output
        assert "STOCKS" in output

    def test_total_calculation(self, capsys):
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

        assert "TOTAL" in output
        assert "$3,000.00" in output   # mkt value total
        assert "+$50.00" in output     # unrealized total


# ---------------------------------------------------------------------------
# Session tests
# ---------------------------------------------------------------------------

class TestInitializeSession:
    @patch("monitor.api_get")
    def test_authenticated(self, mock_get):
        mock_get.side_effect = [
            {"accounts": ["DUXXXXXXX"]},
            {"authenticated": True, "connected": True},
        ]
        mon.initialize_session()  # Should not raise

    @patch("monitor.api_get")
    def test_not_authenticated_exits(self, mock_get):
        mock_get.side_effect = [
            {"accounts": ["DUXXXXXXX"]},
            {"authenticated": False, "connected": True},
        ]
        with pytest.raises(SystemExit):
            mon.initialize_session()
