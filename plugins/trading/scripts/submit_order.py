#!/usr/bin/env python3
"""
Generic IBKR order submitter.

Submits orders from a JSON file (iron_butterfly.py output) or inline CLI args.

Usage from JSON file:
    python submit_order.py iron_butterfly_2026-03-06.json
    python submit_order.py iron_butterfly_2026-03-06.json --dry-run

Usage with inline args:
    python submit_order.py --symbol AAPL --side BUY --quantity 10 --price 150.00
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from ib_async import Contract, LimitOrder, Stock
from ib_client import connect

from ib_client import build_combo, round_to_tick


def display_order(order_data: dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print("  ORDER DETAILS")
    print("=" * 60)
    meta = order_data.get("metadata", {})
    if meta:
        print(f"  Strategy:   {meta.get('strategy', 'N/A')}")
        print(f"  Symbol:     {meta.get('symbol', 'N/A')}")
        if "expiry" in meta:
            print(f"  Expiry:     {meta['expiry']}")
        if "net_credit" in meta:
            print(f"  Net Credit: {meta['net_credit']}")
        if "max_profit" in meta:
            print(f"  Max Profit: ${meta['max_profit']:,.2f}")
        if "max_loss" in meta:
            print(f"  Max Loss:   ${meta['max_loss']:,.2f}")
        if "legs" in meta:
            print(f"\n  Legs:")
            for leg in meta["legs"]:
                label = leg.get("label", f"{leg.get('action')} {leg.get('strike')} {leg.get('right')}")
                print(f"    {leg['action']:>4}  {leg.get('strike', ''):>7}  {leg.get('right', ''):>1}  {label}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit IBKR order.")
    parser.add_argument("file", nargs="?", help="JSON order file")
    parser.add_argument("--symbol", help="Stock symbol for inline orders")
    parser.add_argument("--side", choices=["BUY", "SELL"])
    parser.add_argument("--quantity", type=int)
    parser.add_argument("--price", type=float)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-y", "--yes", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    args = parser.parse_args()

    ib = connect(args.host, args.port)

    if args.file:
        with open(args.file) as f:
            order_data = json.load(f)
        display_order(order_data)

        if args.dry_run:
            print("\n[DRY RUN] Order not submitted.")
            ib.disconnect()
            return

        if not args.yes:
            confirm = input("\nSubmit this order? (yes/no): ").strip().lower()
            if confirm not in ("yes", "y"):
                print("Cancelled.")
                ib.disconnect()
                return

        meta = order_data.get("metadata", {})
        legs = meta.get("legs", [])
        if not legs:
            sys.exit("ERROR: No leg data in metadata.")

        bag = build_combo("SPX", [
            (Contract(conId=leg["conid"], exchange="SMART"), leg["action"])
            for leg in legs
        ])
        price = round_to_tick(-meta.get("net_credit", 0))

        print(f"\nSubmitting: BUY combo LMT @ {price} ...")
        trade = ib.placeOrder(bag, LimitOrder("BUY", 1, price))
        ib.sleep(5)
        print(f"  Status: {trade.orderStatus.status}")
        if trade.orderStatus.status == "Filled":
            print(f"  Filled @ {trade.orderStatus.avgFillPrice:.2f}")

    elif args.symbol and args.side and args.quantity and args.price:
        contract = Stock(args.symbol, "SMART", "USD")
        ib.qualifyContracts(contract)

        print(f"\nSubmitting: {args.side} {args.quantity} {args.symbol} LMT @ {args.price}")
        if not args.yes:
            confirm = input("Confirm? (yes/no): ").strip().lower()
            if confirm not in ("yes", "y"):
                print("Cancelled.")
                ib.disconnect()
                return

        trade = ib.placeOrder(contract, LimitOrder(args.side, args.quantity, args.price))
        ib.sleep(5)
        print(f"  Status: {trade.orderStatus.status}")
    else:
        parser.print_help()
        print("\nProvide a JSON file or all inline arguments.")

    ib.disconnect()


if __name__ == "__main__":
    main()
