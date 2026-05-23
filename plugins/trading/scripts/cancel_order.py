#!/usr/bin/env python3
"""
Cancel IBKR orders.

Usage:
    python cancel_order.py              # list + cancel all
    python cancel_order.py --all        # cancel all without prompt
"""

from __future__ import annotations

import argparse

from ib_client import connect


def main() -> None:
    parser = argparse.ArgumentParser(description="Cancel IBKR orders.")
    parser.add_argument("--all", action="store_true", dest="cancel_all")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    args = parser.parse_args()

    ib = connect(args.host, args.port)
    trades = ib.openTrades()

    if not trades:
        print("No open orders.")
        ib.disconnect()
        return

    print(f"Found {len(trades)} open order(s):\n")
    for t in trades:
        o = t.order
        c = t.contract
        print(f"  [{o.orderId}] {o.action} {o.totalQuantity} {c.symbol} {c.secType} "
              f"@ {o.lmtPrice}  ({t.orderStatus.status})")

    if not args.cancel_all:
        confirm = input("\nCancel all? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("Cancelled.")
            ib.disconnect()
            return

    print("\nCancelling...")
    for t in trades:
        ib.cancelOrder(t.order)
        print(f"  Cancelled order {t.order.orderId}")

    ib.sleep(2)
    print("Done.")
    ib.disconnect()


if __name__ == "__main__":
    main()
