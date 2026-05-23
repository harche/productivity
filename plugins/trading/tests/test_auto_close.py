"""Tests for auto_close.py argument parsing."""

from ib_client import round_to_tick


class TestAutoCloseCalculations:
    def test_profit_target_price(self):
        net_credit = 42.50
        profit_dollars = 300
        quantity = 1
        close_price = net_credit - (profit_dollars / 100.0 / quantity)
        assert round_to_tick(-close_price) == -39.50

    def test_stop_loss_price(self):
        net_credit = 42.50
        stop_dollars = 500
        quantity = 1
        stop_price = net_credit + (stop_dollars / 100.0 / quantity)
        assert round_to_tick(-stop_price) == -47.50

    def test_multi_quantity_profit(self):
        net_credit = 42.50
        profit_dollars = 300
        quantity = 2
        close_price = net_credit - (profit_dollars / 100.0 / quantity)
        assert round_to_tick(-close_price) == -41.00
