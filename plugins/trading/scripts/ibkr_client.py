#!/usr/bin/env python3
"""
Shared IBKR Client Portal Gateway client.

All scripts import from here instead of duplicating API functions.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Any, Optional

import warnings
warnings.filterwarnings("ignore")

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    print("Installing requests ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests"])
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = "https://localhost:5000/v1/api"
SNAPSHOT_STALE_SECONDS = 10


def api_get(path: str, params: Optional[dict] = None, retries: int = 2) -> Any:
    """GET request with retry on 5xx errors."""
    url = f"{BASE_URL}{path}"
    for attempt in range(retries + 1):
        resp = requests.get(url, params=params, verify=False, timeout=15)
        if resp.status_code >= 500 and attempt < retries:
            time.sleep(1)
            continue
        if resp.status_code == 401:
            raise ConnectionError(
                "Session expired (401). Re-authenticate at https://localhost:5000 "
                "or run: python3 start_gateway.py"
            )
        resp.raise_for_status()
        return resp.json()


def api_post(path: str, json_body: Optional[dict] = None, retries: int = 2) -> Any:
    """POST request with retry on 5xx errors."""
    url = f"{BASE_URL}{path}"
    for attempt in range(retries + 1):
        resp = requests.post(url, json=json_body, verify=False, timeout=15)
        if resp.status_code >= 500 and attempt < retries:
            time.sleep(1)
            continue
        if resp.status_code == 401:
            raise ConnectionError(
                "Session expired (401). Re-authenticate at https://localhost:5000 "
                "or run: python3 start_gateway.py"
            )
        resp.raise_for_status()
        return resp.json()


def api_delete(path: str) -> Any:
    """DELETE request."""
    url = f"{BASE_URL}{path}"
    resp = requests.delete(url, verify=False, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _start_keepalive() -> None:
    """Start keepalive.py in the background if not already running."""
    try:
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keepalive.py")
        # Check if a keepalive process is already running
        result = subprocess.run(
            ["pgrep", "-f", script],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return  # already running

        subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass  # non-critical, don't block session init


def initialize_session() -> dict:
    """Initialize iserver session and verify authentication. Returns auth status."""
    accounts = api_get("/iserver/accounts")
    time.sleep(0.15)
    status = api_get("/iserver/auth/status")
    if not status.get("authenticated"):
        sys.exit(
            "ERROR: Not authenticated. Ensure the Client Portal Gateway is running "
            "and you are logged in at https://localhost:5000"
        )
    _start_keepalive()
    return status


def get_account_id() -> str:
    """Get the first portfolio account ID."""
    accounts = api_get("/portfolio/accounts")
    if not accounts:
        sys.exit("ERROR: No accounts found.")
    return accounts[0]["accountId"]


def parse_price(field_val: Any) -> Optional[float]:
    """Parse a price field from market data snapshot. Handles string prefixes like 'C', 'H'."""
    if field_val is None:
        return None
    if isinstance(field_val, (int, float)):
        return float(field_val)
    if isinstance(field_val, str):
        cleaned = field_val.lstrip("CHch")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def get_market_snapshot(conids: list[int], fields: str = "31,84,86") -> dict[int, dict]:
    """
    Get market data snapshot for multiple conids.
    Primes the subscription, waits, then reads.
    Returns {conid: {"bid": float, "ask": float, "last": float, "_updated": int}}.

    Raises ValueError if data appears stale (>SNAPSHOT_STALE_SECONDS old).
    """
    conid_str = ",".join(str(c) for c in conids)
    params = {"conids": conid_str, "fields": fields}

    # Prime
    api_get("/iserver/marketdata/snapshot", params=params)
    time.sleep(2.5)
    # Read
    data = api_get("/iserver/marketdata/snapshot", params=params)

    results: dict[int, dict] = {}
    now_ms = int(time.time() * 1000)

    for snap in (data if isinstance(data, list) else [data]):
        cid = snap.get("conid")
        updated = snap.get("_updated", 0)
        age_seconds = (now_ms - updated) / 1000.0 if updated else None

        results[cid] = {
            "bid": parse_price(snap.get("84")),
            "ask": parse_price(snap.get("86")),
            "last": parse_price(snap.get("31")),
            "_updated": updated,
            "_age_seconds": age_seconds,
            "_stale": age_seconds is not None and age_seconds > SNAPSHOT_STALE_SECONDS,
        }

    return results


def get_combo_snapshot(conidex: str, fields: str = "31,84,86") -> dict:
    """
    Get market data snapshot for a combo order using its conidex.
    Returns {"bid": float|None, "ask": float|None, "last": float|None}.
    """
    body = {"conids": [conidex], "fields": [int(f) for f in fields.split(",")]}
    api_post("/iserver/marketdata/snapshot", json_body=body)
    time.sleep(2.5)
    data = api_post("/iserver/marketdata/snapshot", json_body=body)

    snap = data[0] if isinstance(data, list) and data else {}
    return {
        "bid": parse_price(snap.get("84")),
        "ask": parse_price(snap.get("86")),
        "last": parse_price(snap.get("31")),
    }


def check_staleness(snapshots: dict[int, dict]) -> list[int]:
    """Return list of conids with stale data. Empty list means all fresh."""
    return [cid for cid, data in snapshots.items() if data.get("_stale")]


def handle_order_response(resp: Any) -> Optional[str]:
    """Handle IBKR order response with confirmation chain. Returns order ID or None."""
    max_confirmations = 5
    for _ in range(max_confirmations):
        if not isinstance(resp, list) or not resp:
            break

        first = resp[0]
        oid = first.get("order_id") or first.get("orderId")
        if oid:
            status = first.get("order_status") or first.get("orderStatus")
            print(f"  Order ID: {oid}, Status: {status}")
            return str(oid)

        reply_id = first.get("id")
        if reply_id and first.get("message"):
            for msg in first.get("message", []):
                print(f"  Confirm: {msg}")
            resp = api_post(f"/iserver/reply/{reply_id}", json_body={"confirmed": True})
            continue

        if first.get("error"):
            print(f"  ERROR: {first['error']}")
            return None

        break

    return None


def submit_order(account_id: str, order_body: dict) -> Optional[str]:
    """Submit an order and handle confirmations. Returns order ID or None."""
    resp = api_post(f"/iserver/account/{account_id}/orders", json_body=order_body)
    return handle_order_response(resp)


def cancel_order(account_id: str, order_id: str) -> dict:
    """Cancel an order by ID."""
    return api_delete(f"/iserver/account/{account_id}/order/{order_id}")


def modify_order(account_id: str, order_id: str, modifications: dict) -> Optional[str]:
    """Modify an existing order. Returns new order ID or None."""
    resp = api_post(
        f"/iserver/account/{account_id}/order/{order_id}",
        json_body=modifications,
    )
    return handle_order_response(resp)


def get_live_orders() -> list[dict]:
    """Get all live/recent orders."""
    data = api_get("/iserver/account/orders")
    return data.get("orders", []) if isinstance(data, dict) else []


def get_order_status(order_id: str) -> dict:
    """Get detailed status for a single order."""
    return api_get(f"/iserver/account/order/status/{order_id}")


def get_positions(account_id: str, page: int = 0) -> list[dict]:
    """Get positions for an account (single page)."""
    return api_get(f"/portfolio/{account_id}/positions/{page}")


def get_account_summary(account_id: str) -> dict:
    """Get account summary (balances, margin, buying power)."""
    return api_get(f"/portfolio/{account_id}/summary")


def search_contract(symbol: str) -> dict:
    """Search for a stock/ETF contract by symbol. Returns first match with conid."""
    data = api_get("/trsrv/stocks", params={"symbols": symbol})
    entries = data.get(symbol.upper(), [])
    if not entries or not entries[0].get("contracts"):
        raise ValueError(f"No contracts found for {symbol}")
    contract = entries[0]["contracts"][0]
    return {
        "conid": contract["conid"],
        "exchange": contract.get("exchange"),
        "name": entries[0].get("name"),
    }


def get_option_strikes(underlying_conid: int, month: str, exchange: str = "SMART") -> dict:
    """Get available option strikes. Returns {"call": [...], "put": [...]}."""
    return api_get("/iserver/secdef/strikes", params={
        "conid": underlying_conid, "sectype": "OPT",
        "month": month, "exchange": exchange,
    })


def get_option_contract(
    underlying_conid: int, strike: float, right: str,
    month: str, maturity: str, exchange: str = "SMART",
) -> dict:
    """Get a specific option contract definition."""
    contracts = api_get("/iserver/secdef/info", params={
        "conid": underlying_conid, "sectype": "OPT", "month": month,
        "exchange": exchange, "strike": str(strike), "right": right,
    })
    time.sleep(0.15)

    matched = [c for c in contracts if c.get("maturityDate") == maturity]
    if not matched:
        raise ValueError(
            f"No option contract found: strike={strike} right={right} "
            f"maturity={maturity}. Check that the expiry date is valid "
            f"and the market is open."
        )

    # Prefer SPXW (weekly) over SPX (monthly) for index options
    weeklies = [c for c in matched if c.get("tradingClass") == "SPXW"]
    return weeklies[0] if weeklies else matched[0]
