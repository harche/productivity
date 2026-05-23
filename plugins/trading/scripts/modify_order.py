#!/usr/bin/env python3
"""
Modify an existing IBKR order's price.

Usage:
    python modify_order.py --price -25.50
"""

from __future__ import annotations

import argparse
import sys

from ib_client import connect


def main() -> None:
    parser = argparse.ArgumentParser(description="Modify an existing IBKR order.")
    parser.add_argument("--price", type=float, required=True, help="New limit price")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    args = parser.parse_args()

    ib = connect(args.host, args.port)
    trades = ib.openTrades()

    if not trades:
        print("No open orders to modify.")
        ib.disconnect()
        sys.exit(1)

    print(f"Open orders:\n")
    for i, t in enumerate(trades):
        o = t.order
        c = t.contract
        print(f"  [{i}] Order {o.orderId}: {o.action} {o.totalQuantity} {c.symbol} "
              f"{c.secType} @ {o.lmtPrice}  ({t.orderStatus.status})")

    if len(trades) == 1:
        idx = 0
    else:
        try:
            idx = int(input(f"\nWhich order to modify? [0-{len(trades)-1}]: ").strip())
        except (ValueError, EOFError):
            print("Cancelled.")
            ib.disconnect()
            return

    trade = trades[idx]
    old_price = trade.order.lmtPrice
    trade.order.lmtPrice = args.price
    ib.placeOrder(trade.contract, trade.order)
    ib.sleep(2)

    print(f"\n  Modified order {trade.order.orderId}: price {old_price} -> {args.price}")
    print(f"  New status: {trade.orderStatus.status}")

    ib.disconnect()


if __name__ == "__main__":
    main()
