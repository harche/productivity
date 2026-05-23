"""Tests for monitor.py display formatting."""

from monitor import format_currency, format_pnl, format_pct


class TestFormatCurrency:
    def test_positive(self):
        assert format_currency(1234.56) == "$1,234.56"

    def test_zero(self):
        assert format_currency(0.0) == "$0.00"

    def test_none(self):
        assert format_currency(None) == "N/A"

    def test_negative(self):
        assert format_currency(-500.0) == "$-500.00"


class TestFormatPnl:
    def test_positive(self):
        assert format_pnl(250.0) == "+$250.00"

    def test_negative(self):
        assert format_pnl(-100.0) == "$-100.00"

    def test_zero(self):
        assert format_pnl(0.0) == "+$0.00"

    def test_none(self):
        assert format_pnl(None) == "N/A"


class TestFormatPct:
    def test_positive(self):
        assert format_pct(12.5) == "+12.50%"

    def test_negative(self):
        assert format_pct(-5.3) == "-5.30%"

    def test_none(self):
        assert format_pct(None) == "N/A"
