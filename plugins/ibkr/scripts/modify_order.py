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
from typing import Optional

from ibkr_client import initialize_session, get_account_id, get_order_status, get_live_orders, modify_order


# Map IBKR status response field values to modify API values
ORDER_TYPE_MAP: dict[str, str] = {
    "LIMIT": "LMT", "Limit": "LMT", "LMT": "LMT",
    "MARKET": "MKT", "Market": "MKT", "MKT": "MKT",
    "STP LMT": "STP LMT", "Stop Limit": "STP LMT",
    "STOP": "STP", "Stop": "STP", "STP": "STP",
    "MIDPRICE": "MIDPRICE", "MidPrice": "MIDPRICE",
}

SIDE_MAP: dict[str, str] = {
    "B": "BUY", "BUY": "BUY", "Buy": "BUY",
    "S": "SELL", "SELL": "SELL", "Sell": "SELL",
}

TIF_MAP: dict[str, str] = {
    "CLOSE": "DAY", "DAY": "DAY", "GTC": "GTC", "IOC": "IOC", "OPG": "OPG",
}


def find_order_in_live_orders(order_id: str) -> Optional[dict]:
    """Find an order in live orders list — has more fields than order status."""
    orders = get_live_orders()
    for o in orders:
        if str(o.get("orderId")) == order_id:
            return o
    return None


def display_order_details(label: str, details: dict) -> None:
    """Print order details in a readable format."""
    print(f"\n{'=' * 55}")
    print(f"  {label}")
    print(f"{'=' * 55}")

    fields: list[tuple[str, str]] = [
        ("Order ID",    str(details.get("orderId", details.get("order_id", "N/A")))),
        ("Symbol",      str(details.get("ticker", details.get("symbol", "N/A")))),
        ("Description", str(details.get("orderDesc", details.get("order_description", "N/A")))),
        ("Side",        str(details.get("side", "N/A"))),
        ("Order Type",  str(details.get("orderType", details.get("origOrderType", "N/A")))),
        ("Quantity",    str(details.get("totalSize", details.get("quantity", "N/A")))),
        ("Price",       str(details.get("price", details.get("limit_price", "N/A")))),
        ("Status",      str(details.get("status", details.get("order_status", "N/A")))),
    ]

    for name, value in fields:
        print(f"  {name:<14}  {value}")

    print(f"{'=' * 55}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Modify an existing IBKR order.")
    parser.add_argument("order_id", type=str, help="The order ID to modify.")
    parser.add_argument("--price", type=float, default=None, help="New limit price.")
    parser.add_argument("--quantity", type=int, default=None, help="New quantity.")
    args = parser.parse_args()

    if args.price is None and args.quantity is None:
        print("ERROR: Provide at least --price or --quantity to modify.")
        sys.exit(1)

    initialize_session()
    account_id: str = get_account_id()

    # Get current order from live orders (has conidex, price, side, etc.)
    print(f"Fetching order {args.order_id}...")
    live_order = find_order_in_live_orders(args.order_id)

    if not live_order:
        print(f"ERROR: Order {args.order_id} not found in live orders.")
        sys.exit(1)

    display_order_details("CURRENT ORDER", live_order)

    # Build modification payload with properly mapped field values
    raw_type = str(live_order.get("origOrderType", live_order.get("orderType", "")))
    raw_side = str(live_order.get("side", ""))
    raw_tif = str(live_order.get("timeInForce", "DAY"))

    modifications: dict = {
        "orderType": ORDER_TYPE_MAP.get(raw_type, raw_type),
        "side": SIDE_MAP.get(raw_side, raw_side),
        "tif": TIF_MAP.get(raw_tif, raw_tif),
    }

    # Use conidex for combos, conid for single legs
    conidex = live_order.get("conidex")
    conid = live_order.get("conid")
    if conidex and ";;;" in str(conidex):
        modifications["conidex"] = conidex
    elif conid:
        modifications["conid"] = int(conid)

    # Quantity
    if args.quantity is not None:
        modifications["quantity"] = args.quantity
        print(f"\nChanging quantity to: {args.quantity}")
    else:
        qty = live_order.get("totalSize", live_order.get("remainingQuantity", 1))
        modifications["quantity"] = int(float(qty))

    # Price
    if args.price is not None:
        modifications["price"] = args.price
        print(f"Changing price to: {args.price}")
    else:
        existing_price = live_order.get("price")
        if existing_price:
            modifications["price"] = float(existing_price)

    print("\nSubmitting modification...")
    new_order_id = modify_order(account_id, args.order_id, modifications)

    if new_order_id:
        print(f"\nModification accepted. New order ID: {new_order_id}")
        updated = find_order_in_live_orders(new_order_id)
        if updated:
            display_order_details("UPDATED ORDER", updated)
    else:
        print("\nModification may have failed. Check order status manually.")
        sys.exit(1)


if __name__ == "__main__":
    main()
