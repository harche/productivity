#!/usr/bin/env python3
"""
Generic IBKR order submitter via Client Portal Gateway API.

Submits any order — individual or combo, any ticker, any price — from a JSON file
or inline JSON arguments.

Requires: pip install requests

Usage from JSON file (e.g. output of iron_butterfly.py):
    python submit_order.py iron_butterfly_2026-03-06.json

Usage with inline arguments (single contract):
    python submit_order.py --account DUXXXXXXX --conid 265598 --side BUY \
        --quantity 10 --order-type LMT --price 150.00 --tif DAY

Usage with inline arguments (combo via conidex):
    python submit_order.py --account DUXXXXXXX \
        --conidex "416904;;;854745265/1,849314253/-1,842231145/-1,843303351/1" \
        --side BUY --quantity 1 --order-type LMT --price -72.20 --tif DAY

JSON file format:
{
    "account_id": "DUXXXXXXX",
    "orders": [
        {
            "conid": 265598,          // for single contract
            "conidex": "...",         // for combo (mutually exclusive with conid)
            "orderType": "LMT",
            "side": "BUY",
            "price": 150.00,
            "quantity": 10,
            "tif": "DAY"
        }
    ],
    "metadata": { ... }              // optional, for display only
}
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Optional

import ibkr_client


def display_order(order_data: dict[str, Any]) -> None:
    """Display the order details before submission."""
    print("\n" + "=" * 60)
    print("  ORDER DETAILS")
    print("=" * 60)
    print(f"  Account:    {order_data['account_id']}")

    for i, order in enumerate(order_data["orders"]):
        if len(order_data["orders"]) > 1:
            print(f"\n  --- Order {i+1} ---")
        contract = order.get("conidex") or order.get("conid")
        print(f"  Contract:   {contract}")
        print(f"  Side:       {order['side']}")
        print(f"  Type:       {order['orderType']}")
        print(f"  Quantity:   {order['quantity']}")
        if "price" in order:
            print(f"  Price:      {order['price']}")
        if "auxPrice" in order:
            print(f"  Aux Price:  {order['auxPrice']}")
        print(f"  TIF:        {order['tif']}")
        if order.get("outsideRTH"):
            print(f"  Outside RTH: Yes")

    meta = order_data.get("metadata", {})
    if meta:
        print(f"\n  Strategy:   {meta.get('strategy', 'N/A')}")
        print(f"  Symbol:     {meta.get('symbol', 'N/A')}")
        if "expiry" in meta:
            print(f"  Expiry:     {meta['expiry']}")
        if "net_credit" in meta:
            print(f"  Net Credit: {meta['net_credit']}")
        if "max_profit" in meta:
            print(f"  Max Profit: ${meta['max_profit']:,.2f}")
        if "max_loss" in meta:
            print(f"  Max Loss:   ${meta['max_loss']:,.2f}")
        if "ratio" in meta:
            print(f"  Ratio:      {meta['ratio']}x")
        if "legs" in meta:
            print(f"\n  Legs:")
            for leg in meta["legs"]:
                label = leg.get("label", f"{leg.get('action')} {leg.get('strike')} {leg.get('right')}")
                print(f"    {leg['action']:>4}  {leg.get('strike', ''):>7}  {leg.get('right', ''):>1}  {label}")

    print("=" * 60)


def fetch_live_prices(order_data: dict[str, Any]) -> None:
    """On dry run, fetch live prices for combo legs and compare to order."""
    meta = order_data.get("metadata", {})
    legs = meta.get("legs", [])
    if not legs:
        return

    conids = [leg["conid"] for leg in legs if "conid" in leg]
    if not conids:
        return

    try:
        snapshots = ibkr_client.get_market_snapshot(conids)
        stale_conids = ibkr_client.check_staleness(snapshots)
        if stale_conids:
            print(f"\n  [Warning: stale data for conids {stale_conids}]")
    except Exception:
        print("\n  [Could not fetch live prices]")
        return

    print(f"\n  {'LIVE PRICES':^56}")
    print(f"  {'-' * 56}")
    print(f"  {'Leg':<22} {'Saved Bid':>9} {'Live Bid':>9} {'Live Ask':>9}")
    print(f"  {'-' * 56}")
    for leg in legs:
        cid = leg.get("conid")
        lp = snapshots.get(cid, {})
        saved_bid = f"{leg['bid']:.2f}" if leg.get("bid") is not None else "N/A"
        live_bid = f"{lp['bid']:.2f}" if lp.get("bid") is not None else "N/A"
        live_ask = f"{lp['ask']:.2f}" if lp.get("ask") is not None else "N/A"
        label = leg.get("label", f"{leg.get('strike')} {leg.get('right')}")
        print(f"  {label:<22} {saved_bid:>9} {live_bid:>9} {live_ask:>9}")
    print(f"  {'-' * 56}")


def verify_order(order_id: str) -> None:
    """Check and display the final order status."""
    print(f"\n[3/3] Verifying order {order_id} ...")
    time.sleep(1.5)
    try:
        status = ibkr_client.get_order_status(order_id)
        print(f"       Status:      {status.get('order_status', 'N/A')}")
        print(f"       Description: {status.get('order_description_with_contract', status.get('order_description', 'N/A'))}")
        print(f"       Filled:      {status.get('size_and_fills', 'N/A')}")

        desc3 = status.get("contract_description_3", "")
        if desc3:
            print(f"       Legs:")
            for leg in desc3.split("<br>"):
                if leg.strip():
                    print(f"         {leg.strip()}")
    except Exception as e:
        print(f"       Could not verify: {e}")


def load_from_file(filepath: str) -> dict[str, Any]:
    """Load order data from a JSON file."""
    with open(filepath) as f:
        return json.load(f)


def build_from_args(args: argparse.Namespace) -> dict[str, Any]:
    """Build order data from CLI arguments."""
    order: dict[str, Any] = {
        "orderType": args.order_type,
        "side": args.side,
        "quantity": args.quantity,
        "tif": args.tif,
    }

    if args.conidex:
        order["conidex"] = args.conidex
    elif args.conid:
        order["conid"] = args.conid
    else:
        sys.exit("ERROR: Must provide either --conid or --conidex")

    if args.price is not None:
        order["price"] = args.price
    if args.aux_price is not None:
        order["auxPrice"] = args.aux_price
    if args.outside_rth:
        order["outsideRTH"] = True

    return {
        "account_id": args.account,
        "orders": [order],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Submit any IBKR order (individual or combo) from JSON file or CLI args."
    )

    # JSON file mode
    parser.add_argument("file", nargs="?", help="JSON order file (from iron_butterfly.py or hand-crafted)")

    # Inline mode
    parser.add_argument("--account", help="IBKR account ID (e.g. DUXXXXXXX)")
    parser.add_argument("--conid", type=int, help="Contract ID for single-leg orders")
    parser.add_argument("--conidex", help="Combo conidex string for multi-leg orders")
    parser.add_argument("--side", choices=["BUY", "SELL"], help="Order side")
    parser.add_argument("--quantity", type=int, help="Number of shares/contracts")
    parser.add_argument("--order-type", default="LMT",
                        choices=["LMT", "STP", "STP LMT", "MIDPRICE", "LOC"],
                        help="Order type (default: LMT)")
    parser.add_argument("--price", type=float, help="Limit price")
    parser.add_argument("--aux-price", type=float, help="Stop/aux price")
    parser.add_argument("--tif", default="DAY", choices=["DAY", "GTC", "IOC", "OPG"],
                        help="Time in force (default: DAY)")
    parser.add_argument("--outside-rth", action="store_true", help="Allow outside regular trading hours")
    parser.add_argument("--dry-run", action="store_true", help="Display order details without submitting")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    # Build order data from file or CLI args
    if args.file:
        order_data = load_from_file(args.file)
    elif args.account and (args.conid or args.conidex) and args.side and args.quantity:
        order_data = build_from_args(args)
    else:
        parser.print_help()
        print("\nProvide either a JSON file or all required inline arguments.")
        sys.exit(1)

    print("[1/3] Initializing session ...")
    status = ibkr_client.initialize_session()
    print(f"       Authenticated: {status.get('authenticated')}, Connected: {status.get('connected')}")

    display_order(order_data)

    if args.dry_run:
        fetch_live_prices(order_data)
        print("\n[DRY RUN] Order not submitted.")
        return

    if not args.yes:
        confirm = input("\nSubmit this order? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("Order cancelled.")
            return

    account_id = order_data["account_id"]
    orders_body = {"orders": order_data["orders"]}

    print(f"\n[2/3] Submitting order to account {account_id} ...")
    order_id = ibkr_client.submit_order(account_id, orders_body)

    if order_id:
        verify_order(order_id)
        print("\nDone.")
    else:
        print("\nOrder submission failed or returned no order ID.")
        sys.exit(1)


if __name__ == "__main__":
    main()
