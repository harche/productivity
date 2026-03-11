#!/usr/bin/env python3
"""
Auto-close for IBKR combo positions via Client Portal Gateway API.

Calculates the closing limit price from a profit target or stop-loss,
then submits a standing limit order. IBKR handles execution automatically.

For profit target: closing price = net_credit - (target$ / 100 / quantity)
For stop-loss: closing price = net_credit + (loss$ / 100 / quantity)

Usage:
    python auto_close.py iron_butterfly_2026-03-11.json --profit 300
    python auto_close.py iron_butterfly_2026-03-11.json --stop-loss 500
    python auto_close.py iron_butterfly_2026-03-11.json --profit 300 --stop-loss 500
"""

import argparse
import json
import subprocess
import sys
import time

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


def api_post(path, json_body=None, retries=2):
    url = f"{BASE_URL}{path}"
    for attempt in range(retries + 1):
        resp = requests.post(url, json=json_body, verify=False, timeout=15)
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


def handle_order_response(resp):
    """Handle IBKR order response with confirmation chain."""
    max_confirmations = 5
    for _ in range(max_confirmations):
        if not isinstance(resp, list) or not resp:
            break

        first = resp[0]
        oid = first.get("order_id") or first.get("orderId")
        if oid:
            status = first.get("order_status") or first.get("orderStatus")
            print(f"  Order ID: {oid}, Status: {status}")
            return oid

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


def submit_closing_order(account_id, conidex, quantity, limit_price, label):
    """Submit a standing limit order to close the combo."""
    order = {
        "orders": [{
            "conidex": conidex,
            "orderType": "LMT",
            "side": "SELL",
            "price": limit_price,
            "quantity": quantity,
            "tif": "DAY",
        }]
    }

    print(f"  Submitting {label}: SELL {quantity}x combo LMT @ {limit_price:.2f} ...")
    resp = api_post(f"/iserver/account/{account_id}/orders", json_body=order)
    return handle_order_response(resp)


def main():
    parser = argparse.ArgumentParser(
        description="Submit standing limit orders to auto-close IBKR combo positions."
    )
    parser.add_argument("file", help="JSON order file (from iron_butterfly.py or strategy builder)")
    parser.add_argument("--profit", type=float, metavar="DOLLARS",
                        help="Target profit in dollars (e.g., 300)")
    parser.add_argument("--stop-loss", type=float, metavar="DOLLARS",
                        help="Max loss in dollars (e.g., 500)")
    args = parser.parse_args()

    if args.profit is None and args.stop_loss is None:
        parser.error("Must specify at least one of --profit or --stop-loss")

    with open(args.file) as f:
        order_data = json.load(f)

    meta = order_data.get("metadata", {})
    net_credit = meta.get("net_credit")
    max_profit = meta.get("max_profit")
    max_loss = meta.get("max_loss")
    account_id = order_data.get("account_id")
    conidex = order_data["orders"][0].get("conidex")
    quantity = order_data["orders"][0].get("quantity", 1)

    if net_credit is None or conidex is None:
        sys.exit("ERROR: Order file missing metadata (net_credit) or conidex.")

    print(f"Auto-close setup")
    print(f"  Strategy:     {meta.get('strategy', 'N/A')}")
    print(f"  Symbol:       {meta.get('symbol', 'N/A')}")
    print(f"  Net Credit:   {net_credit}")
    print(f"  Max Profit:   ${max_profit:,.2f}")
    print(f"  Max Loss:     ${max_loss:,.2f}")
    print(f"  Quantity:     {quantity}")
    print()

    initialize_session()

    orders_submitted = []

    if args.profit is not None:
        # To keep $profit, we close at: net_credit - (profit / 100 / quantity)
        close_price = net_credit - (args.profit / 100.0 / quantity)
        close_price = round(close_price, 2)
        print(f"  Profit target: ${args.profit:,.2f}")
        print(f"  Close price:   {close_price:.2f} (net_credit {net_credit} - {args.profit/100/quantity:.2f})")
        oid = submit_closing_order(account_id, conidex, quantity, -close_price, "PROFIT TARGET")
        if oid:
            orders_submitted.append(("Profit target", oid))
        print()

    if args.stop_loss is not None:
        # To cap loss at $stop_loss, we close at: net_credit + (stop_loss / 100 / quantity)
        close_price = net_credit + (args.stop_loss / 100.0 / quantity)
        close_price = round(close_price, 2)
        print(f"  Stop loss:     ${args.stop_loss:,.2f}")
        print(f"  Close price:   {close_price:.2f} (net_credit {net_credit} + {args.stop_loss/100/quantity:.2f})")
        oid = submit_closing_order(account_id, conidex, quantity, -close_price, "STOP LOSS")
        if oid:
            orders_submitted.append(("Stop loss", oid))
        print()

    if orders_submitted:
        print("Standing orders submitted:")
        for label, oid in orders_submitted:
            print(f"  {label}: Order ID {oid}")
        print("\nIBKR will execute automatically when the price hits. Done.")
    else:
        print("No orders submitted.")
        sys.exit(1)


if __name__ == "__main__":
    main()
