"""
Live integration tests — run against actual IB Gateway.

Safe: read-only operations only. No orders placed.

Run with: pytest tests/test_live_integration.py -v -m live
Skip with: pytest tests/ -v -m "not live"

Requires IB Gateway running on port 4002.
"""

import pytest

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def ib():
    from ib_client import connect
    ib = connect("127.0.0.1", 4002)
    yield ib
    ib.disconnect()


class TestConnection:
    def test_connected(self, ib):
        assert ib.isConnected()

    def test_managed_accounts(self, ib):
        accounts = ib.managedAccounts()
        assert len(accounts) > 0

    def test_account_values(self, ib):
        values = ib.accountValues()
        assert len(values) > 0
        tags = {v.tag for v in values}
        assert "NetLiquidation" in tags


class TestMarketData:
    def test_spx_price(self, ib):
        from ib_client import get_spx_price
        price = get_spx_price(ib)
        assert price > 1000

    def test_expiry_lookup(self, ib):
        from ib_client import get_expiry
        expiry = get_expiry(ib, 3)
        assert len(expiry) == 8
        assert expiry.startswith("202")

    def test_qualify_option(self, ib):
        from ib_async import Option
        from ib_client import get_expiry
        expiry = get_expiry(ib, 1)
        opt = Option("SPX", expiry, 7000, "C", "SMART", tradingClass="SPXW")
        qualified = ib.qualifyContracts(opt)
        assert len(qualified) == 1
        assert qualified[0].conId > 0


class TestPortfolio:
    def test_positions(self, ib):
        positions = ib.positions()
        assert isinstance(positions, list)

    def test_portfolio(self, ib):
        portfolio = ib.portfolio()
        assert isinstance(portfolio, list)
