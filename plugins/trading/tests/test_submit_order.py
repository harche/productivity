"""Tests for submit_order.py display logic."""

from submit_order import display_order


class TestDisplayOrder:
    def test_displays_metadata(self, sample_order_json, capsys):
        display_order(sample_order_json)
        out = capsys.readouterr().out
        assert "iron_butterfly" in out
        assert "SPX" in out
        assert "42.5" in out
        assert "4,250.00" in out

    def test_displays_legs(self, sample_order_json, capsys):
        display_order(sample_order_json)
        out = capsys.readouterr().out
        assert "Long Put" in out
        assert "Short Call" in out
        assert "BUY" in out
        assert "SELL" in out

    def test_empty_metadata(self, capsys):
        display_order({})
        out = capsys.readouterr().out
        assert "ORDER DETAILS" in out
