#!/usr/bin/env python3
"""
Cancel one or more IBKR orders.

Usage:
    python3 cancel_order.py 3212818                    # cancel single order
    python3 cancel_order.py 3212818 3212819            # cancel multiple
    python3 cancel_order.py --all                      # cancel all open orders
"""

from __future__ import annotations

import argparse
import sys

from ibkr_client import initialize_session, get_account_id, get_live_orders, cancel_order


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cancel one or more IBKR orders.")
    parser.add_argument(
        "order_ids",
        nargs="*",
        type=str,
        help="One or more order IDs to cancel.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="cancel_all",
        help="Cancel all open (non-filled) orders.",
    )
    return parser.parse_args()


def cancel_single_order(account_id: str, order_id: str) -> bool:
    """Cancel a single order and print the result. Returns True on success."""
    try:
        result: dict = cancel_order(account_id, order_id)
        msg: str = result.get("msg", result.get("message", str(result)))
        print(f"  Order {order_id}: {msg}")
        return True
    except Exception as exc:
        print(f"  Order {order_id}: FAILED - {exc}")
        return False


def cancel_all_open_orders(account_id: str) -> None:
    """Fetch all live orders, filter to non-filled, and cancel each."""
    orders: list[dict] = get_live_orders()

    non_filled_statuses: set[str] = {
        "PreSubmitted",
        "Submitted",
        "PendingSubmit",
        "PendingCancel",
        "ApiPending",
        "ApiCancelled",
        "Inactive",
    }

    open_orders: list[dict] = [
        o for o in orders if o.get("status") in non_filled_statuses
    ]

    if not open_orders:
        print("No open orders to cancel.")
        return

    print(f"Found {len(open_orders)} open order(s):\n")
    for order in open_orders:
        oid: str = str(order.get("orderId", ""))
        ticker: str = order.get("ticker", order.get("symbol", "N/A"))
        side: str = order.get("side", "N/A")
        qty: str = str(order.get("remainingQuantity", order.get("totalSize", "N/A")))
        status: str = order.get("status", "N/A")
        price: str = str(order.get("price", "N/A"))
        print(f"  [{oid}] {side} {qty} {ticker} @ {price}  (status: {status})")

    print("\nCancelling all open orders...\n")

    success_count: int = 0
    for order in open_orders:
        oid = str(order.get("orderId", ""))
        if cancel_single_order(account_id, oid):
            success_count += 1

    print(f"\nCancelled {success_count}/{len(open_orders)} order(s).")


def main() -> None:
    args: argparse.Namespace = parse_args()

    if not args.cancel_all and not args.order_ids:
        print("ERROR: Provide at least one order ID, or use --all to cancel all open orders.")
        sys.exit(1)

    initialize_session()
    account_id: str = get_account_id()

    if args.cancel_all:
        cancel_all_open_orders(account_id)
    else:
        order_ids: list[str] = args.order_ids
        print(f"Cancelling {len(order_ids)} order(s)...\n")

        success_count: int = 0
        for oid in order_ids:
            if cancel_single_order(account_id, oid):
                success_count += 1

        print(f"\nCancelled {success_count}/{len(order_ids)} order(s).")


if __name__ == "__main__":
    main()
