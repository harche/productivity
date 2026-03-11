"""
Live integration tests — run against actual IBKR gateway.

These tests are safe: read-only operations + whatif order validation.
No real orders are placed.

Run with: pytest tests/test_live_integration.py -v -m live
Skip with: pytest tests/ -v -m "not live"

Requires IBKR Client Portal Gateway running and authenticated.
"""

from __future__ import annotations

import pytest

# Mark all tests in this module as "live"
pytestmark = pytest.mark.live


def gateway_available() -> bool:
    """Check if the IBKR gateway is reachable and authenticated."""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            return s.connect_ex(("localhost", 5000)) == 0
    except Exception:
        return False


skip_no_gateway = pytest.mark.skipif(
    not gateway_available(),
    reason="IBKR gateway not running on localhost:5000"
)


@skip_no_gateway
class TestSessionIntegration:
    def test_auth_status(self) -> None:
        from ibkr_client import api_get
        status = api_get("/iserver/auth/status")
        assert status.get("authenticated") is True
        assert status.get("connected") is True

    def test_initialize_session(self) -> None:
        from ibkr_client import initialize_session
        status = initialize_session()
        assert status["authenticated"] is True

    def test_get_account_id(self) -> None:
        from ibkr_client import initialize_session, get_account_id
        initialize_session()
        account_id = get_account_id()
        assert account_id.startswith("DU") or account_id.startswith("U")


@skip_no_gateway
class TestContractSearchIntegration:
    def test_search_aapl(self) -> None:
        from ibkr_client import initialize_session, search_contract
        initialize_session()
        result = search_contract("AAPL")
        assert result["conid"] == 265598
        assert "APPLE" in result["name"].upper()

    def test_search_spy(self) -> None:
        from ibkr_client import initialize_session, search_contract
        initialize_session()
        result = search_contract("SPY")
        assert result["conid"] == 756733

    def test_search_invalid_symbol(self) -> None:
        from ibkr_client import initialize_session, search_contract
        initialize_session()
        with pytest.raises(ValueError, match="No contracts found"):
            search_contract("ZZZZZZXXX")


@skip_no_gateway
class TestMarketDataIntegration:
    def test_snapshot_returns_prices(self) -> None:
        from ibkr_client import initialize_session, get_market_snapshot
        initialize_session()
        # AAPL conid = 265598
        snapshots = get_market_snapshot([265598])
        assert 265598 in snapshots
        snap = snapshots[265598]
        # At least one price field should be populated
        assert snap.get("last") is not None or snap.get("bid") is not None

    def test_staleness_detection_returns_list(self) -> None:
        from ibkr_client import initialize_session, get_market_snapshot, check_staleness
        initialize_session()
        snapshots = get_market_snapshot([265598])
        stale = check_staleness(snapshots)
        # check_staleness returns a list (may be non-empty if market is closed)
        assert isinstance(stale, list)


@skip_no_gateway
class TestAccountIntegration:
    def test_account_summary(self) -> None:
        from ibkr_client import initialize_session, get_account_id, get_account_summary
        initialize_session()
        account_id = get_account_id()
        summary = get_account_summary(account_id)
        # Should have at least net liquidation value
        assert "netliquidation" in summary

    def test_positions(self) -> None:
        from ibkr_client import initialize_session, get_account_id, get_positions
        initialize_session()
        account_id = get_account_id()
        positions = get_positions(account_id)
        # positions is a list (may be empty)
        assert isinstance(positions, list)


@skip_no_gateway
class TestOrderWhatIfIntegration:
    """Validate order payloads against IBKR without placing real orders."""

    def test_whatif_lmt_order_accepted(self) -> None:
        """A valid LMT order should not return an error from whatif."""
        from ibkr_client import initialize_session, get_account_id, api_post
        initialize_session()
        account_id = get_account_id()

        order = {
            "orders": [{
                "conid": 265598,  # AAPL
                "orderType": "LMT",
                "side": "BUY",
                "quantity": 1,
                "price": 100.00,
                "tif": "DAY",
            }]
        }

        result = api_post(f"/iserver/account/{account_id}/orders/whatif", json_body=order)
        assert result.get("error") is None

    def test_whatif_stp_lmt_order_accepted(self) -> None:
        """A valid STP LMT order should be accepted by whatif."""
        from ibkr_client import initialize_session, get_account_id, api_post
        initialize_session()
        account_id = get_account_id()

        order = {
            "orders": [{
                "conid": 265598,  # AAPL
                "orderType": "STP LMT",
                "side": "SELL",
                "quantity": 1,
                "price": 90.00,
                "auxPrice": 95.00,
                "tif": "DAY",
            }]
        }

        result = api_post(f"/iserver/account/{account_id}/orders/whatif", json_body=order)
        assert result.get("error") is None

    def test_whatif_invalid_order_type_rejected(self) -> None:
        """An invalid order type like STP_LIMIT should be rejected with 400."""
        from ibkr_client import initialize_session, get_account_id, api_post
        from requests.exceptions import HTTPError
        initialize_session()
        account_id = get_account_id()

        order = {
            "orders": [{
                "conid": 265598,
                "orderType": "STP_LIMIT",  # Wrong! Should be "STP LMT"
                "side": "SELL",
                "quantity": 1,
                "price": 90.00,
                "auxPrice": 95.00,
                "tif": "DAY",
            }]
        }

        with pytest.raises(HTTPError, match="400"):
            api_post(f"/iserver/account/{account_id}/orders/whatif", json_body=order)

    def test_whatif_combo_lmt_accepted(self) -> None:
        """A combo LMT order should be accepted by whatif."""
        from ibkr_client import initialize_session, get_account_id, api_post
        import ibkr_client
        initialize_session()
        account_id = get_account_id()

        # Search for SPX option contracts to build a real combo
        # Use a simple 2-leg vertical for testing
        import time
        data = ibkr_client.api_get("/iserver/secdef/info", params={
            "conid": 416904, "sectype": "OPT", "month": "APR26",
            "exchange": "SMART", "strike": "6800", "right": "P",
        })
        time.sleep(0.15)

        if not data:
            pytest.skip("No option contracts available for test")

        conid1 = data[0]["conid"]

        data2 = ibkr_client.api_get("/iserver/secdef/info", params={
            "conid": 416904, "sectype": "OPT", "month": "APR26",
            "exchange": "SMART", "strike": "6750", "right": "P",
        })
        time.sleep(0.15)

        if not data2:
            pytest.skip("No option contracts available for test")

        conid2 = data2[0]["conid"]

        order = {
            "orders": [{
                "conidex": f"416904;;;{conid1}/-1,{conid2}/1",
                "orderType": "LMT",
                "side": "BUY",
                "quantity": 1,
                "price": -5.00,
                "tif": "DAY",
            }]
        }

        result = api_post(f"/iserver/account/{account_id}/orders/whatif", json_body=order)
        assert result.get("error") is None
