#!/usr/bin/env python3
"""
IBKR Position Monitor via Client Portal Gateway API.

Displays all open positions with live P/L, market value, and price data.

Usage:
    python monitor.py
    python monitor.py --watch 30       # refresh every 30 seconds
    python monitor.py --symbol SPX     # filter by symbol
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

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


def api_get(path, params=None, retries=2):
    url = f"{BASE_URL}{path}"
    for attempt in range(retries + 1):
        resp = requests.get(url, params=params, verify=False, timeout=15)
        if resp.status_code >= 500 and attempt < retries:
            time.sleep(1)
            continue
        resp.raise_for_status()
        return resp.json()


def initialize_session():
    api_get("/iserver/accounts")
    status = api_get("/iserver/auth/status")
    if not status.get("authenticated"):
        sys.exit("ERROR: Not authenticated. Ensure the Client Portal Gateway is running and logged in.")
    return status


def get_account_id():
    accounts = api_get("/portfolio/accounts")
    return accounts[0]["accountId"]


def get_positions(account_id, symbol_filter=None):
    positions = []
    page = 0
    while True:
        page_data = api_get(f"/portfolio/{account_id}/positions/{page}")
        if not page_data:
            break
        positions.extend(page_data)
        page += 1
        if len(page_data) < 30:
            break
        time.sleep(0.15)

    if symbol_filter:
        filt = symbol_filter.upper()
        positions = [p for p in positions if filt in (p.get("ticker", "") or "").upper()
                     or filt in (p.get("contractDesc", "") or "").upper()]

    return positions


def format_currency(value):
    if value is None:
        return "N/A"
    return f"${value:,.2f}"


def format_pnl(value):
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}${value:,.2f}"


def format_pct(value):
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def display_positions(positions, account_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'=' * 90}")
    print(f"  POSITIONS — {account_id}    {now}")
    print(f"{'=' * 90}")

    if not positions:
        print("  No open positions.")
        print(f"{'=' * 90}")
        return

    # Group by asset class
    groups = {}
    for p in positions:
        asset = p.get("assetClass", "OTHER")
        groups.setdefault(asset, []).append(p)

    total_mktval = 0
    total_unrealized = 0

    for asset_class in sorted(groups.keys()):
        group = groups[asset_class]
        label = {"OPT": "OPTIONS", "STK": "STOCKS", "FUT": "FUTURES",
                 "CASH": "CASH", "WAR": "WARRANTS", "BOND": "BONDS"}.get(asset_class, asset_class)
        print(f"\n  --- {label} ---")
        print(f"  {'Description':<36} {'Pos':>6} {'Mkt Price':>10} {'Mkt Value':>12} {'Unrealized':>12} {'% P/L':>8}")
        print(f"  {'-' * 86}")

        for p in sorted(group, key=lambda x: x.get("ticker", "")):
            desc = p.get("contractDesc", p.get("ticker", "???"))
            if len(desc) > 35:
                desc = desc[:32] + "..."
            pos = p.get("position", 0)
            mkt_price = p.get("mktPrice", None)
            mkt_value = p.get("mktValue", None)
            unrealized = p.get("unrealizedPnl", None)
            avg_cost = p.get("avgCost", None)

            pct = None
            if unrealized is not None and avg_cost is not None and pos != 0:
                cost_basis = avg_cost * abs(pos)
                if cost_basis != 0:
                    pct = (unrealized / cost_basis) * 100

            price_str = f"{mkt_price:.2f}" if mkt_price is not None else "N/A"
            print(f"  {desc:<36} {pos:>6.0f} {price_str:>10} {format_currency(mkt_value):>12} {format_pnl(unrealized):>12} {format_pct(pct):>8}")

            if mkt_value is not None:
                total_mktval += mkt_value
            if unrealized is not None:
                total_unrealized += unrealized

        print(f"  {'-' * 86}")

    print(f"\n  {'TOTAL':<36} {'':>6} {'':>10} {format_currency(total_mktval):>12} {format_pnl(total_unrealized):>12}")
    print(f"{'=' * 90}")


def main():
    parser = argparse.ArgumentParser(description="Monitor IBKR positions with live P/L.")
    parser.add_argument("--symbol", "-s", help="Filter positions by symbol (e.g., SPX, AAPL)")
    parser.add_argument("--watch", "-w", type=int, metavar="SECS",
                        help="Refresh every N seconds (default: one-shot)")
    args = parser.parse_args()

    initialize_session()
    account_id = get_account_id()

    if args.watch:
        try:
            while True:
                os.system("clear" if os.name != "nt" else "cls")
                positions = get_positions(account_id, args.symbol)
                display_positions(positions, account_id)
                print(f"\n  Refreshing every {args.watch}s ... (Ctrl+C to stop)")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        positions = get_positions(account_id, args.symbol)
        display_positions(positions, account_id)


if __name__ == "__main__":
    main()
