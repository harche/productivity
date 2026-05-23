"""Shared fixtures for IBKR trading plugin tests."""

import json
import os
import sys
import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "live: tests that require a live IB Gateway")


@pytest.fixture
def sample_strategy():
    """A realistic iron butterfly strategy dict."""
    return {
        "strategy_name": "iron_butterfly",
        "expiry": "2026-03-11",
        "expiry_str": "20260311",
        "trading_class": "SPXW",
        "spx_price": 6777.50,
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
        "wing_width": 130,
        "net_credit": 42.50,
        "max_profit": 4250.00,
        "max_loss": 8750.00,
        "ratio": 2.06,
        "lower_breakeven": 6732.50,
        "upper_breakeven": 6822.50,
    }


@pytest.fixture
def sample_order_json(sample_strategy):
    """Order JSON as saved by iron_butterfly.py."""
    return {
        "metadata": {
            "strategy": sample_strategy["strategy_name"],
            "symbol": "SPX",
            "expiry": sample_strategy["expiry"],
            "net_credit": sample_strategy["net_credit"],
            "max_profit": sample_strategy["max_profit"],
            "max_loss": sample_strategy["max_loss"],
            "ratio": sample_strategy["ratio"],
            "legs": sample_strategy["legs"],
        }
    }


@pytest.fixture
def order_file(tmp_path, sample_order_json):
    """Write sample order to temp file and return path."""
    path = tmp_path / "iron_butterfly_2026-03-11.json"
    path.write_text(json.dumps(sample_order_json, indent=2))
    return str(path)
