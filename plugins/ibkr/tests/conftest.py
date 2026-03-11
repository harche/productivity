"""Shared fixtures for IBKR plugin tests."""

import json
import os
import sys
import pytest

# Add scripts directory to path so we can import modules
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "live: tests that require a live IBKR gateway")


@pytest.fixture
def sample_order_data():
    """A realistic iron butterfly order JSON."""
    return {
        "account_id": "DUXXXXXXX",
        "orders": [
            {
                "conidex": "416904;;;859216550/1,851292423/-1,852416651/-1,852416755/1",
                "orderType": "LMT",
                "side": "BUY",
                "price": -42.50,
                "tif": "DAY",
                "quantity": 1,
            }
        ],
        "metadata": {
            "strategy": "iron_butterfly",
            "symbol": "SPX",
            "expiry": "2026-03-11",
            "net_credit": 42.50,
            "max_profit": 4250.00,
            "max_loss": 8750.00,
            "ratio": 2.06,
            "legs": [
                {"action": "BUY", "strike": 6645, "right": "P", "conid": 859216550,
                 "bid": 1.05, "ask": 1.10, "label": "Long Put (wing)"},
                {"action": "SELL", "strike": 6775, "right": "P", "conid": 851292423,
                 "bid": 21.90, "ask": 22.10, "label": "Short Put (ATM)"},
                {"action": "SELL", "strike": 6780, "right": "C", "conid": 852416651,
                 "bid": 21.90, "ask": 22.10, "label": "Short Call (ATM)"},
                {"action": "BUY", "strike": 6910, "right": "C", "conid": 852416755,
                 "bid": 0.15, "ask": 0.20, "label": "Long Call (wing)"},
            ],
        },
    }


@pytest.fixture
def order_file(tmp_path, sample_order_data):
    """Write sample order data to a temp file and return the path."""
    path = tmp_path / "iron_butterfly_2026-03-11.json"
    path.write_text(json.dumps(sample_order_data, indent=2))
    return str(path)


@pytest.fixture
def mock_auth_status():
    """Standard authenticated status response."""
    return {"authenticated": True, "connected": True}


@pytest.fixture
def mock_accounts():
    """Standard accounts response."""
    return {"accounts": ["DUXXXXXXX"]}


@pytest.fixture
def mock_portfolio_accounts():
    """Standard portfolio accounts response."""
    return [{"accountId": "DUXXXXXXX"}]
