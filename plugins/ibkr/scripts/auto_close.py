#!/usr/bin/env python3
"""
Auto-close positions via IBKR Client Portal Gateway API.

Monitors a position and closes it when a profit target or stop-loss is hit.
For combo orders (e.g., iron butterfly), checks if the combo has an ask price.
If yes, closes the full combo. If no ask, closes only the short legs individually.

Usage:
    python auto_close.py iron_butterfly_2026-03-11.json --profit-target 50
    python auto_close.py iron_butterfly_2026-03-11.json --stop-loss 80
    python auto_close.py iron_butterfly_2026-03-11.json --profit-target 50 --stop-loss 80 --poll 30
"""

import argparse
import json
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


def api_post(path, json_body=None, retries=2):
    url = f"{BASE_URL}{path}"
    for attempt in range(retries + 1):
        resp = requests.post(url, json=json_body, verify=False, timeout=15)
        if resp.status_code >= 500 and attempt < retries:
            time.sleep(1)
            continue
        resp.raise_for_status()
        return resp.json()


def parse_price(field_val):
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


def initialize_session():
    api_get("/iserver/accounts")
    status = api_get("/iserver/auth/status")
    if not status.get("authenticated"):
        sys.exit("ERROR: Not authenticated. Ensure the Client Portal Gateway is running and logged in.")


def get_leg_prices(conids):
    """Get bid/ask for multiple conids."""
    conid_str = ",".join(str(c) for c in conids)
    params = {"conids": conid_str, "fields": "31,84,86"}
    api_get("/iserver/marketdata/snapshot", params=params)
    time.sleep(2.5)
    data = api_get("/iserver/marketdata/snapshot", params=params)

    results = {}
    for snap in (data if isinstance(data, list) else [data]):
        cid = snap.get("conid")
        results[cid] = {
            "bid": parse_price(snap.get("84")),
            "ask": parse_price(snap.get("86")),
            "last": parse_price(snap.get("31")),
        }
    return results


def compute_combo_pnl(legs, prices):
    """Compute current combo value from leg prices to estimate P/L."""
    combo_value = 0
    for leg in legs:
        cid = leg["conid"]
        p = prices.get(cid, {})
        if leg["action"] == "SELL":
            # We sold this leg — to close we'd buy at ask
            ask = p.get("ask")
            if ask is not None:
                combo_value -= ask
        else:
            # We bought this leg — to close we'd sell at bid
            bid = p.get("bid")
            if bid is not None:
                combo_value += bid
    return combo_value


def get_combo_quote(conidex):
    """Get the combo order's own bid/ask as a single instrument."""
    # Parse conidex: "416904;;;conid1/1,conid2/-1,conid3/-1,conid4/1"
    parts = conidex.split(";;;")
    underlying_conid = int(parts[0])
    leg_defs = []
    for lp in parts[1].split(","):
        cid, ratio = lp.split("/")
        leg_defs.append({"conid": int(cid), "ratio": int(ratio)})

    # Register combo to get a combo conid
    combo_resp = api_post("/iserver/secdef/combo", json_body={
        "conid": underlying_conid,
        "legs": leg_defs,
    })

    combo_conid = None
    if isinstance(combo_resp, dict):
        combo_conid = combo_resp.get("conid")
    elif isinstance(combo_resp, list) and combo_resp:
        combo_conid = combo_resp[0].get("conid")

    if not combo_conid:
        return None

    # Snapshot the combo conid for bid/ask
    params = {"conids": str(combo_conid), "fields": "84,86"}
    api_get("/iserver/marketdata/snapshot", params=params)
    time.sleep(2.5)
    data = api_get("/iserver/marketdata/snapshot", params=params)

    snap = data[0] if isinstance(data, list) and data else data
    return {
        "bid": parse_price(snap.get("84")),
        "ask": parse_price(snap.get("86")),
    }


def submit_combo_close(account_id, order_data, quantity, combo_quote):
    """Close the full combo order at limit (match the ask to ensure fill)."""
    original_order = order_data["orders"][0]
    conidex = original_order["conidex"]
    limit_price = combo_quote.get("ask")

    close_order = {
        "orders": [{
            "conidex": conidex,
            "orderType": "LMT",
            "side": "SELL",
            "price": limit_price,
            "quantity": quantity,
            "tif": "DAY",
        }]
    }

    print(f"  Submitting COMBO close (SELL {quantity}x full combo LMT @ {limit_price}) ...")
    resp = api_post(f"/iserver/account/{account_id}/orders", json_body=close_order)
    return handle_order_response(resp)


def submit_short_legs_close(account_id, legs, quantity, prices):
    """Close only the short legs in parallel at limit (match the ask)."""
    import concurrent.futures

    short_legs = [leg for leg in legs if leg["action"] == "SELL"]

    def close_leg(leg):
        cid = leg["conid"]
        ask = prices.get(cid, {}).get("ask")
        order = {
            "orders": [{
                "conid": cid,
                "orderType": "LMT",
                "side": "BUY",
                "price": ask,
                "quantity": quantity,
                "tif": "DAY",
            }]
        }
        label = f"{leg.get('strike', '?')} {leg.get('right', '?')}"
        print(f"  Closing short leg: BUY {quantity}x {label} (conid {cid}) LMT @ {ask} ...")
        resp = api_post(f"/iserver/account/{account_id}/orders", json_body=order)
        return handle_order_response(resp)

    order_ids = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(short_legs)) as executor:
        futures = {executor.submit(close_leg, leg): leg for leg in short_legs}
        for future in concurrent.futures.as_completed(futures):
            oid = future.result()
            if oid:
                order_ids.append(oid)

    return order_ids


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


def main():
    parser = argparse.ArgumentParser(
        description="Auto-close IBKR positions at profit target or stop-loss."
    )
    parser.add_argument("file", help="JSON order file (from iron_butterfly.py or strategy builder)")
    parser.add_argument("--profit-target", type=float, metavar="PCT",
                        help="Close when unrealized profit reaches this %% of max profit (e.g., 50)")
    parser.add_argument("--stop-loss", type=float, metavar="PCT",
                        help="Close when unrealized loss reaches this %% of max loss (e.g., 80)")
    parser.add_argument("--poll", type=int, default=60,
                        help="Check interval in seconds (default: 60)")
    args = parser.parse_args()

    if args.profit_target is None and args.stop_loss is None:
        parser.error("Must specify at least one of --profit-target or --stop-loss")

    with open(args.file) as f:
        order_data = json.load(f)

    meta = order_data.get("metadata", {})
    legs = meta.get("legs", [])
    max_profit = meta.get("max_profit")
    max_loss = meta.get("max_loss")
    net_credit = meta.get("net_credit")
    account_id = order_data.get("account_id")
    quantity = order_data["orders"][0].get("quantity", 1)

    if not legs or max_profit is None or max_loss is None:
        sys.exit("ERROR: Order file missing metadata (legs, max_profit, max_loss).")

    conids = [leg["conid"] for leg in legs]

    profit_threshold = (args.profit_target / 100.0) * max_profit if args.profit_target else None
    loss_threshold = (args.stop_loss / 100.0) * max_loss if args.stop_loss else None

    print(f"Auto-close monitor started")
    print(f"  Strategy:       {meta.get('strategy', 'N/A')}")
    print(f"  Symbol:         {meta.get('symbol', 'N/A')}")
    print(f"  Max Profit:     ${max_profit:,.2f}")
    print(f"  Max Loss:       ${max_loss:,.2f}")
    print(f"  Net Credit:     {net_credit}")
    if profit_threshold:
        print(f"  Profit Target:  {args.profit_target}% = ${profit_threshold:,.2f}")
    if loss_threshold:
        print(f"  Stop Loss:      {args.stop_loss}% = ${loss_threshold:,.2f}")
    print(f"  Poll Interval:  {args.poll}s")
    print(f"  Quantity:       {quantity}")
    print()

    initialize_session()

    try:
        while True:
            now = datetime.now().strftime("%H:%M:%S")
            prices = get_leg_prices(conids)

            # Cost to close: buy back shorts at ask, sell longs at bid
            close_cost = 0
            price_strs = []
            for leg in legs:
                cid = leg["conid"]
                p = prices.get(cid, {})
                if leg["action"] == "SELL":
                    val = p.get("ask")
                    if val is not None:
                        close_cost += val
                    price_strs.append(f"{leg.get('strike','')} {leg.get('right','')}: ask={val}")
                else:
                    val = p.get("bid")
                    if val is not None:
                        close_cost -= val
                    price_strs.append(f"{leg.get('strike','')} {leg.get('right','')}: bid={val}")

            # Unrealized P/L = net_credit - close_cost (what we'd pay to close)
            unrealized_pnl = (net_credit - close_cost) * 100 * quantity

            pnl_str = f"+${unrealized_pnl:,.2f}" if unrealized_pnl >= 0 else f"-${abs(unrealized_pnl):,.2f}"
            print(f"  [{now}] P/L: {pnl_str}  (close cost: {close_cost:.2f})")

            triggered = None
            if profit_threshold and unrealized_pnl >= profit_threshold:
                triggered = "PROFIT TARGET"
            elif loss_threshold and unrealized_pnl <= -loss_threshold:
                triggered = "STOP LOSS"

            if triggered:
                print(f"\n  >>> {triggered} HIT! P/L: {pnl_str} <<<\n")

                conidex = order_data["orders"][0]["conidex"]
                combo_quote = get_combo_quote(conidex)

                has_ask = combo_quote and combo_quote.get("ask") is not None
                if has_ask:
                    print(f"  Combo bid={combo_quote.get('bid')} ask={combo_quote.get('ask')} — closing full combo at LMT.")
                    oid = submit_combo_close(account_id, order_data, quantity, combo_quote)
                    if oid:
                        print(f"\n  Full combo close submitted (Order ID: {oid}).")
                    else:
                        print("\n  Combo close failed. Falling back to short legs only.")
                        oids = submit_short_legs_close(account_id, legs, quantity, prices)
                        print(f"\n  Short legs closed ({len(oids)} orders).")
                else:
                    print("  Combo has no ask — closing short legs only at LMT (in parallel).")
                    oids = submit_short_legs_close(account_id, legs, quantity, prices)
                    print(f"\n  Short legs closed ({len(oids)} orders).")

                print("  Auto-close complete.")
                return

            time.sleep(args.poll)

    except KeyboardInterrupt:
        print("\n\nStopped by user.")


if __name__ == "__main__":
    main()
