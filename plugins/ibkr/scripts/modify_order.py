#!/usr/bin/env python3
"""
Modify an existing IBKR order's price or quantity.

Usage:
    python3 modify_order.py 3212818 --price -25.50     # change limit price
    python3 modify_order.py 3212818 --quantity 2        # change quantity
"""

from __future__ import annotations

import argparse
import sys

from ibkr_client import initialize_session, get_account_id, get_order_status, modify_order


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Modify an existing IBKR order.")
    parser.add_argument(
        "order_id",
        type=str,
        help="The order ID to modify.",
    )
    parser.add_argument(
        "--price",
        type=float,
        default=None,
        help="New limit price for the order.",
    )
    parser.add_argument(
        "--quantity",
        type=int,
        default=None,
        help="New quantity for the order.",
    )
    return parser.parse_args()


def display_order_details(label: str, details: dict) -> None:
    """Print order details in a readable format."""
    print(f"\n{'=' * 50}")
    print(f"  {label}")
    print(f"{'=' * 50}")

    fields: list[tuple[str, str]] = [
        ("Order ID",   str(details.get("orderId", details.get("order_id", "N/A")))),
        ("Symbol",     str(details.get("ticker", details.get("symbol", "N/A")))),
        ("Side",       str(details.get("side", details.get("orderType", "N/A")))),
        ("Order Type", str(details.get("orderType", details.get("order_type", "N/A")))),
        ("Quantity",   str(details.get("totalSize", details.get("quantity", "N/A")))),
        ("Remaining",  str(details.get("remainingQuantity", details.get("remaining", "N/A")))),
        ("Limit Price", str(details.get("price", details.get("limitPrice", "N/A")))),
        ("Avg Price",  str(details.get("avgPrice", details.get("average_price", "N/A")))),
        ("Status",     str(details.get("status", details.get("order_status", "N/A")))),
        ("Last Updated", str(details.get("lastExecutionTime_r", details.get("lastModified", "N/A")))),
    ]

    max_label_len: int = max(len(f[0]) for f in fields)
    for name, value in fields:
        print(f"  {name:<{max_label_len}}  {value}")

    print(f"{'=' * 50}")


def main() -> None:
    args: argparse.Namespace = parse_args()

    if args.price is None and args.quantity is None:
        print("ERROR: Provide at least --price or --quantity to modify.")
        sys.exit(1)

    initialize_session()
    account_id: str = get_account_id()
    order_id: str = args.order_id

    # Fetch current order details
    print(f"Fetching current details for order {order_id}...")
    current: dict = get_order_status(order_id)
    display_order_details("CURRENT ORDER", current)

    # Build modification payload
    modifications: dict = {}

    # Carry forward required fields from the current order
    conid: int | str | None = current.get("conid")
    order_type: str | None = current.get("orderType")
    side: str | None = current.get("side")
    tif: str | None = current.get("timeInForce", current.get("tif"))

    if conid is not None:
        modifications["conid"] = int(conid)
    if order_type is not None:
        modifications["orderType"] = order_type
    if side is not None:
        modifications["side"] = side
    if tif is not None:
        modifications["tif"] = tif

    # Apply requested changes
    if args.price is not None:
        modifications["price"] = args.price
        print(f"\nChanging price to: {args.price}")

    if args.quantity is not None:
        modifications["quantity"] = args.quantity
        print(f"Changing quantity to: {args.quantity}")
    else:
        # Carry forward existing quantity
        existing_qty: int | str | None = current.get("totalSize", current.get("quantity"))
        if existing_qty is not None:
            modifications["quantity"] = int(existing_qty)

    # Submit modification
    print("\nSubmitting modification...")
    new_order_id: str | None = modify_order(account_id, order_id, modifications)

    if new_order_id:
        print(f"\nModification accepted. New order ID: {new_order_id}")

        # Fetch updated order details
        updated: dict = get_order_status(new_order_id)
        display_order_details("UPDATED ORDER", updated)
    else:
        print("\nModification may have failed. Check order status manually.")
        sys.exit(1)


if __name__ == "__main__":
    main()
