#!/usr/bin/env python3
"""
Auto-close for IBKR combo positions via Client Portal Gateway API.

Submits standing orders for profit target and/or stop-loss.
IBKR handles execution automatically — no polling needed.

Profit target: LMT order at net_credit - (target$ / 100 / quantity)
Stop-loss: STP LMT order — triggers at stop price, fills at stop + buffer

Usage:
    python auto_close.py iron_butterfly_2026-03-11.json --profit 300
    python auto_close.py iron_butterfly_2026-03-11.json --stop-loss 500
    python auto_close.py iron_butterfly_2026-03-11.json --profit 300 --stop-loss 500
    python auto_close.py iron_butterfly_2026-03-11.json --stop-loss 500 --stop-buffer 3.0
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from ibkr_client import initialize_session, submit_order


def submit_profit_order(
    account_id: str, conidex: str, quantity: int, limit_price: float
) -> Optional[str]:
    """Submit a standing limit order for profit target."""
    order: dict = {
        "orders": [{
            "conidex": conidex,
            "orderType": "LMT",
            "side": "SELL",
            "price": limit_price,
            "quantity": quantity,
            "tif": "DAY",
        }]
    }

    print(f"  Submitting PROFIT TARGET: SELL {quantity}x combo LMT @ {limit_price:.2f} ...")
    return submit_order(account_id, order)


def submit_stop_loss_order(
    account_id: str, conidex: str, quantity: int, stop_price: float, limit_price: float
) -> Optional[str]:
    """Submit a stop-limit order for stop-loss. Triggers at stop_price, fills at limit_price."""
    order: dict = {
        "orders": [{
            "conidex": conidex,
            "orderType": "STP LMT",
            "side": "SELL",
            "price": limit_price,
            "auxPrice": stop_price,
            "quantity": quantity,
            "tif": "DAY",
        }]
    }

    print(f"  Submitting STOP LOSS: SELL {quantity}x combo STP LMT stop={stop_price:.2f} limit={limit_price:.2f} ...")
    return submit_order(account_id, order)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Submit standing limit orders to auto-close IBKR combo positions."
    )
    parser.add_argument("file", help="JSON order file (from iron_butterfly.py or strategy builder)")
    parser.add_argument("--profit", type=float, metavar="DOLLARS",
                        help="Target profit in dollars (e.g., 300)")
    parser.add_argument("--stop-loss", type=float, metavar="DOLLARS",
                        help="Max loss in dollars (e.g., 500)")
    parser.add_argument("--stop-buffer", type=float, default=2.0, metavar="DOLLARS",
                        help="Buffer between stop and limit price in $/spread (default: 2.0)")
    args = parser.parse_args()

    if args.profit is None and args.stop_loss is None:
        parser.error("Must specify at least one of --profit or --stop-loss")

    with open(args.file) as f:
        order_data: dict = json.load(f)

    meta: dict = order_data.get("metadata", {})
    net_credit: Optional[float] = meta.get("net_credit")
    max_profit: Optional[float] = meta.get("max_profit")
    max_loss: Optional[float] = meta.get("max_loss")
    account_id: Optional[str] = order_data.get("account_id")
    conidex: Optional[str] = order_data["orders"][0].get("conidex")
    quantity: int = order_data["orders"][0].get("quantity", 1)

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

    orders_submitted: list[tuple[str, str]] = []

    if args.profit is not None:
        # To keep $profit, we close at: net_credit - (profit / 100 / quantity)
        close_price: float = net_credit - (args.profit / 100.0 / quantity)
        close_price = round(close_price, 2)
        print(f"  Profit target: ${args.profit:,.2f}")
        print(f"  Close price:   {close_price:.2f} (net_credit {net_credit} - {args.profit/100/quantity:.2f})")
        oid = submit_profit_order(account_id, conidex, quantity, -close_price)
        if oid:
            orders_submitted.append(("Profit target (LMT)", oid))
        print()

    if args.stop_loss is not None:
        # Stop triggers at: net_credit + (stop_loss / 100 / quantity)
        # Limit fills at: stop + buffer (gives room to fill)
        stop_price: float = net_credit + (args.stop_loss / 100.0 / quantity)
        stop_price = round(stop_price, 2)
        limit_price: float = round(stop_price + args.stop_buffer, 2)
        print(f"  Stop loss:     ${args.stop_loss:,.2f}")
        print(f"  Stop price:    {stop_price:.2f} (triggers when cost to close hits this)")
        print(f"  Limit price:   {limit_price:.2f} (stop + {args.stop_buffer:.2f} buffer)")
        oid = submit_stop_loss_order(account_id, conidex, quantity, -stop_price, -limit_price)
        if oid:
            orders_submitted.append(("Stop loss (STP LMT)", oid))
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
