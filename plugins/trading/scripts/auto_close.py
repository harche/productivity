#!/usr/bin/env python3
"""
Auto-close for IBKR combo positions.

Submits standing profit target and/or stop-loss orders using OCA groups.

Usage:
    python auto_close.py iron_butterfly_2026-03-11.json --profit 300
    python auto_close.py iron_butterfly_2026-03-11.json --stop-loss 500
    python auto_close.py iron_butterfly_2026-03-11.json --profit 300 --stop-loss 500
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from ib_async import Contract, LimitOrder, Order
from ib_client import connect

from ib_client import build_combo, round_to_tick


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit auto-close orders for combo positions.")
    parser.add_argument("file", help="JSON order file (from iron_butterfly.py)")
    parser.add_argument("--profit", type=float, metavar="DOLLARS")
    parser.add_argument("--stop-loss", type=float, metavar="DOLLARS")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    args = parser.parse_args()

    if args.profit is None and args.stop_loss is None:
        parser.error("Must specify at least one of --profit or --stop-loss")

    with open(args.file) as f:
        meta = json.load(f).get("metadata", {})

    net_credit = meta.get("net_credit")
    legs = meta.get("legs", [])
    quantity = meta.get("quantity", 1)

    if net_credit is None or not legs:
        sys.exit("ERROR: Order file missing metadata (net_credit or legs).")

    print(f"Auto-close: {meta.get('strategy', 'N/A')}  credit={net_credit}")

    ib = connect(args.host, args.port)
    bag = build_combo("SPX", [
        (Contract(conId=leg["conid"], exchange="SMART"), leg["action"])
        for leg in legs
    ])

    oca_group = f"oca_SPX_{int(time.time())}"

    if args.profit is not None:
        close_price = net_credit - (args.profit / 100.0 / quantity)
        profit_order = LimitOrder("SELL", quantity, round_to_tick(-close_price))
        if args.stop_loss is not None:
            profit_order.ocaGroup = oca_group
            profit_order.ocaType = 1
        ib.placeOrder(bag, profit_order)
        print(f"  Profit target: SELL @ {round_to_tick(-close_price)} (${args.profit:,.0f})")

    if args.stop_loss is not None:
        stop_price = net_credit + (args.stop_loss / 100.0 / quantity)
        stop_order = Order()
        stop_order.action = "SELL"
        stop_order.totalQuantity = quantity
        stop_order.orderType = "STP LMT"
        stop_order.auxPrice = round_to_tick(-stop_price)
        stop_order.lmtPrice = round_to_tick(-(stop_price + 2))
        if args.profit is not None:
            stop_order.ocaGroup = oca_group
            stop_order.ocaType = 1
        ib.placeOrder(bag, stop_order)
        print(f"  Stop loss: STP LMT stop={-stop_price:.2f} (${args.stop_loss:,.0f})")

    if args.profit is not None and args.stop_loss is not None:
        print(f"  OCA Group: {oca_group} (one cancels the other)")

    ib.sleep(2)
    print("Done.")
    ib.disconnect()


if __name__ == "__main__":
    main()
