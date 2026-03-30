"""Tests for monitor.py — position monitoring."""

from unittest.mock import patch, MagicMock, call

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


class TestRefreshPrices:
    """Tests for _refresh_prices — live snapshot refresh with combo detection."""

    def _make_opt(self, ticker: str, conid: int, position: float,
                  mkt_price: float = 10.0, avg_cost: float = 900.0,
                  multiplier: float = 100.0) -> dict:
        return {
            "ticker": ticker, "conid": conid, "position": position,
            "mktPrice": mkt_price, "mktValue": mkt_price * position * multiplier,
            "unrealizedPnl": (mkt_price * position * multiplier) - (avg_cost * position),
            "avgCost": avg_cost, "assetClass": "OPT", "multiplier": multiplier,
        }

    def _make_stk(self, ticker: str, conid: int, position: float,
                  mkt_price: float = 150.0, avg_cost: float = 145.0) -> dict:
        return {
            "ticker": ticker, "conid": conid, "position": position,
            "mktPrice": mkt_price, "mktValue": mkt_price * position,
            "unrealizedPnl": (mkt_price * position) - (avg_cost * position),
            "avgCost": avg_cost, "assetClass": "STK", "multiplier": 1,
        }

    @patch("monitor.api_get")
    def test_skips_combo_legs(self, mock_api: MagicMock) -> None:
        """Multi-leg OPT positions on same ticker should NOT be refreshed."""
        positions = [
            self._make_opt("SPX", 1001, -1, mkt_price=9.5),   # short put
            self._make_opt("SPX", 1002, -1, mkt_price=10.0),  # short call
            self._make_opt("SPX", 1003, 1, mkt_price=0.5),    # long put
            self._make_opt("SPX", 1004, 1, mkt_price=0.3),    # long call
        ]
        original_prices = [p["mktPrice"] for p in positions]

        mon._refresh_prices(positions)

        # api_get should NOT have been called — all legs are combo
        mock_api.assert_not_called()
        # Prices should remain unchanged
        assert [p["mktPrice"] for p in positions] == original_prices

    @patch("monitor.time.sleep")
    @patch("monitor.api_get")
    def test_refreshes_single_stock(self, mock_api: MagicMock, mock_sleep: MagicMock) -> None:
        """A single stock position should be refreshed with live data."""
        positions = [self._make_stk("AAPL", 265598, 100, mkt_price=150.0, avg_cost=145.0)]

        mock_api.side_effect = [
            # Prime call
            [{"conid": 265598}],
            # Read call with fresh data
            [{"conid": 265598, "31": "155.00", "84": "154.90", "86": "155.10"}],
        ]

        mon._refresh_prices(positions)

        assert positions[0]["mktPrice"] == 155.0
        assert positions[0]["mktValue"] == 155.0 * 100 * 1.0
        assert positions[0]["unrealizedPnl"] == (155.0 * 100) - (145.0 * 100)

    @patch("monitor.time.sleep")
    @patch("monitor.api_get")
    def test_refreshes_single_option(self, mock_api: MagicMock, mock_sleep: MagicMock) -> None:
        """A single option position (not part of a combo) should be refreshed."""
        positions = [self._make_opt("AAPL", 5001, -1, mkt_price=5.0, avg_cost=400.0)]

        mock_api.side_effect = [
            [{"conid": 5001}],
            [{"conid": 5001, "31": "4.50", "84": "4.40", "86": "4.60"}],
        ]

        mon._refresh_prices(positions)

        assert positions[0]["mktPrice"] == 4.5
        assert positions[0]["mktValue"] == 4.5 * -1 * 100.0
        assert positions[0]["unrealizedPnl"] == (4.5 * -1 * 100.0) - (400.0 * -1)

    @patch("monitor.time.sleep")
    @patch("monitor.api_get")
    def test_mixed_combo_and_stock(self, mock_api: MagicMock, mock_sleep: MagicMock) -> None:
        """Combo legs skipped, but stock on same ticker still refreshed."""
        positions = [
            # Iron butterfly legs — should be skipped
            self._make_opt("SPX", 1001, -1, mkt_price=9.5),
            self._make_opt("SPX", 1002, -1, mkt_price=10.0),
            self._make_opt("SPX", 1003, 1, mkt_price=0.5),
            self._make_opt("SPX", 1004, 1, mkt_price=0.3),
            # Stock — should be refreshed
            self._make_stk("AAPL", 265598, 50, mkt_price=150.0, avg_cost=140.0),
        ]

        mock_api.side_effect = [
            [{"conid": 265598}],
            [{"conid": 265598, "31": "160.00", "84": "159.90", "86": "160.10"}],
        ]

        mon._refresh_prices(positions)

        # SPX combo legs unchanged
        assert positions[0]["mktPrice"] == 9.5
        assert positions[1]["mktPrice"] == 10.0
        assert positions[2]["mktPrice"] == 0.5
        assert positions[3]["mktPrice"] == 0.3
        # AAPL stock refreshed
        assert positions[4]["mktPrice"] == 160.0

    @patch("monitor.time.sleep")
    @patch("monitor.api_get")
    def test_single_option_refreshed_while_combo_skipped(self, mock_api: MagicMock, mock_sleep: MagicMock) -> None:
        """Single AAPL option refreshed; multi-leg SPX combo skipped."""
        positions = [
            self._make_opt("SPX", 1001, -1),
            self._make_opt("SPX", 1002, 1),
            self._make_opt("AAPL", 2001, -1, mkt_price=3.0, avg_cost=250.0),
        ]

        mock_api.side_effect = [
            [{"conid": 2001}],
            [{"conid": 2001, "31": "2.80", "84": "2.70", "86": "2.90"}],
        ]

        mon._refresh_prices(positions)

        # SPX combo legs unchanged
        assert positions[0]["mktPrice"] == 10.0
        assert positions[1]["mktPrice"] == 10.0
        # AAPL single option refreshed
        assert positions[2]["mktPrice"] == 2.8

    def test_no_active_positions(self) -> None:
        """No positions with non-zero qty — should return without API calls."""
        positions = [
            {"ticker": "SPX", "conid": 1001, "position": 0, "assetClass": "OPT"},
        ]
        # Should not raise — just returns early
        mon._refresh_prices(positions)

    def test_empty_positions(self) -> None:
        """Empty list — should return without error."""
        mon._refresh_prices([])

    @patch("monitor.time.sleep")
    @patch("monitor.api_get")
    def test_falls_back_to_mid_price(self, mock_api: MagicMock, mock_sleep: MagicMock) -> None:
        """When last price is missing, use mid of bid/ask."""
        positions = [self._make_stk("AAPL", 265598, 100, mkt_price=150.0, avg_cost=145.0)]

        mock_api.side_effect = [
            [{"conid": 265598}],
            [{"conid": 265598, "84": "154.00", "86": "156.00"}],  # no field 31
        ]

        mon._refresh_prices(positions)

        assert positions[0]["mktPrice"] == 155.0  # mid of 154 and 156

    @patch("monitor.time.sleep")
    @patch("monitor.api_get")
    def test_skips_when_no_price_data(self, mock_api: MagicMock, mock_sleep: MagicMock) -> None:
        """When snapshot has no price fields, position is left unchanged."""
        positions = [self._make_stk("AAPL", 265598, 100, mkt_price=150.0, avg_cost=145.0)]

        mock_api.side_effect = [
            [{"conid": 265598}],
            [{"conid": 265598}],  # no price fields at all
        ]

        mon._refresh_prices(positions)

        assert positions[0]["mktPrice"] == 150.0  # unchanged

    @patch("monitor.time.sleep")
    @patch("monitor.api_get")
    def test_string_multiplier(self, mock_api: MagicMock, mock_sleep: MagicMock) -> None:
        """Multiplier returned as string should be handled."""
        positions = [{
            "ticker": "AAPL", "conid": 265598, "position": -1,
            "mktPrice": 5.0, "mktValue": -500.0, "unrealizedPnl": 0,
            "avgCost": 500.0, "assetClass": "OPT", "multiplier": "100",
        }]

        mock_api.side_effect = [
            [{"conid": 265598}],
            [{"conid": 265598, "31": "4.00", "84": "3.90", "86": "4.10"}],
        ]

        mon._refresh_prices(positions)

        assert positions[0]["mktPrice"] == 4.0
        assert positions[0]["mktValue"] == 4.0 * -1 * 100.0

    @patch("monitor.time.sleep")
    @patch("monitor.api_get")
    def test_none_multiplier(self, mock_api: MagicMock, mock_sleep: MagicMock) -> None:
        """None multiplier should default to 1.0."""
        positions = [{
            "ticker": "AAPL", "conid": 265598, "position": 100,
            "mktPrice": 150.0, "mktValue": 15000.0, "unrealizedPnl": 0,
            "avgCost": 145.0, "assetClass": "STK", "multiplier": None,
        }]

        mock_api.side_effect = [
            [{"conid": 265598}],
            [{"conid": 265598, "31": "155.00", "84": "154.90", "86": "155.10"}],
        ]

        mon._refresh_prices(positions)

        assert positions[0]["mktPrice"] == 155.0
        assert positions[0]["mktValue"] == 155.0 * 100 * 1.0
