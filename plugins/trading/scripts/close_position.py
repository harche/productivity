#!/usr/bin/env python3
"""
Close an IBKR combo position and cancel related standing orders.

Can close from an order JSON file (from iron_butterfly.py) or directly
from live positions by specifying strikes.

Usage:
    python close_position.py iron_butterfly_2026-03-12.json
    python close_position.py --strikes 7410P,7465P,7510C,7565C
    python close_position.py --strikes 7450P,7475P,7520C,7545C -y
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Optional

import time

from ibkr_client import (
    cancel_order,
    get_combo_snapshot,
    get_live_orders,
    get_market_snapshot,
    get_order_status,
    get_positions,
    get_account_id,
    initialize_session,
    submit_order,
)

SPX_CONID = 416904


def parse_strikes(strikes_str: str) -> list[tuple[int, str]]:
    """Parse '7410P,7465P,7510C,7565C' into [(7410, 'P'), (7465, 'P'), ...]."""
    result = []
    for s in strikes_str.split(","):
        s = s.strip().upper()
        m = re.match(r"^(\d+)([PC])$", s)
        if not m:
            sys.exit(f"ERROR: Invalid strike format '{s}'. Expected e.g. 7410P or 7520C.")
        result.append((int(m.group(1)), m.group(2)))
    return result


def build_legs_from_positions(account_id: str, strikes: list[tuple[int, str]]) -> tuple[list[dict], str, int]:
    """Match strikes against live positions and build leg data.

    Returns (legs, conidex, quantity).
    """
    positions = get_positions(account_id)
    matched = []

    for target_strike, target_right in strikes:
        right_code = "P" if target_right == "P" else "C"

        found = False
        for pos in positions:
            desc = pos.get("contractDesc", "")
            if "SPX" not in desc:
                continue
            # contractDesc format: "SPX    MAY2026 7410 P [SPXW  260522P07410000 100]"
            if f" {target_strike} {right_code} " in desc:
                position = pos.get("position", 0)
                if position == 0:
                    continue
                action = "BUY" if position > 0 else "SELL"
                matched.append({
                    "conid": pos["conid"],
                    "strike": target_strike,
                    "right": target_right,
                    "action": action,
                    "position": position,
                    "label": f"{'Long' if position > 0 else 'Short'} {target_right.replace('P','Put').replace('C','Call')} ({target_strike})",
                })
                found = True
                break

        if not found:
            sys.exit(f"ERROR: No open SPX position found for {target_strike}{target_right}")

    quantity = int(min(abs(m["position"]) for m in matched))

    conidex_parts = []
    for m in matched:
        ratio = 1 if m["action"] == "BUY" else -1
        conidex_parts.append(f"{m['conid']}/{ratio}")
    conidex = f"{SPX_CONID};;;{','.join(conidex_parts)}"

    legs = [{
        "conid": m["conid"],
        "strike": m["strike"],
        "right": m["right"],
        "action": m["action"],
        "label": m["label"],
    } for m in matched]

    return legs, conidex, quantity


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Close an IBKR combo position and cancel related standing orders."
    )
    parser.add_argument("file", nargs="?", default=None,
                        help="JSON order file (from iron_butterfly.py). Not needed with --strikes.")
    parser.add_argument("--strikes", type=str, default=None,
                        help="Close by live positions: comma-separated strikes, e.g. 7410P,7465P,7510C,7565C")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    if not args.file and not args.strikes:
        parser.error("Either provide an order JSON file or use --strikes.")

    initialize_session()

    if args.strikes:
        account_id = get_account_id()
        strike_list = parse_strikes(args.strikes)
        print(f"Matching strikes against live positions: {args.strikes}")
        legs, conidex, quantity = build_legs_from_positions(account_id, strike_list)
        net_credit = 0
        print(f"  Found {len(legs)} legs, quantity={quantity}")
        print()
    else:
        with open(args.file) as f:
            order_data: dict = json.load(f)
        meta: dict = order_data.get("metadata", {})
        account_id = order_data["account_id"]
        conidex = order_data["orders"][0]["conidex"]
        quantity = order_data["orders"][0].get("quantity", 1)
        legs = meta.get("legs", [])
        net_credit = meta.get("net_credit", 0)

        if not legs:
            sys.exit("ERROR: No leg data in metadata. Cannot calculate close price.")

        print(f"Close position: {meta.get('strategy', 'combo')} {meta.get('symbol', '')} {meta.get('expiry', '')}")
        print(f"  Quantity: {quantity}")
        print()

    # Fetch live prices for all legs
    conids = [leg["conid"] for leg in legs]
    print("Fetching live prices ...")
    snapshots = get_market_snapshot(conids)

    # Calculate close price
    # To close: reverse each leg (BUY becomes SELL, SELL becomes BUY)
    # Cost = sum of (ask for legs we buy back) - sum of (bid for legs we sell)
    close_cost = 0.0
    print()
    print(f"  {'Leg':<22} {'Action':<6} {'Close':<6} {'Bid':>8} {'Ask':>8} {'Used':>8}")
    print(f"  {'-' * 60}")

    for leg in legs:
        cid = leg["conid"]
        snap = snapshots.get(cid, {})
        bid = snap.get("bid")
        ask = snap.get("ask")
        action = leg["action"]

        if action == "SELL":
            # We sold this leg, need to BUY it back at ask
            price_used = ask
            close_action = "BUY"
            if price_used is not None:
                close_cost += price_used
        else:
            # We bought this leg, need to SELL it at bid
            price_used = bid
            close_action = "SELL"
            if price_used is not None:
                close_cost -= price_used

        bid_s = f"{bid:.2f}" if bid is not None else "N/A"
        ask_s = f"{ask:.2f}" if ask is not None else "N/A"
        used_s = f"{price_used:.2f}" if price_used is not None else "N/A"
        label = leg.get("label", f"{leg.get('strike')} {leg.get('right')}")
        print(f"  {label:<22} {action:<6} {close_action:<6} {bid_s:>8} {ask_s:>8} {used_s:>8}")

    # Identify short legs — these are the risk and must be closed
    short_legs = [l for l in legs if l["action"] == "SELL"]

    # Build reverse conidex (flip the ratios)
    base, _, leg_str = conidex.partition(";;;")
    reversed_parts = []
    for part in leg_str.split(","):
        cid, ratio = part.rsplit("/", 1)
        flipped = str(-int(ratio))
        reversed_parts.append(f"{cid}/{flipped}")
    reverse_conidex = f"{base};;;{','.join(reversed_parts)}"

    # Check combo liquidity
    print(f"\nChecking combo liquidity ...")
    combo_snap = get_combo_snapshot(reverse_conidex)
    combo_bid = combo_snap.get("bid")
    combo_ask = combo_snap.get("ask")
    has_combo_liquidity = combo_bid is not None and combo_ask is not None

    close_cost = round(close_cost, 2)
    print(f"  {'-' * 60}")
    print(f"  Close cost (legs):    {close_cost:.2f}")
    if has_combo_liquidity:
        combo_close_price = combo_ask
        print(f"  Combo bid={combo_bid}  ask={combo_ask}")
        print(f"  Close price (limit):  {combo_close_price:.2f}")
    else:
        combo_close_price = None
        print(f"  Combo: no liquidity (bid/ask missing)")
    if net_credit:
        effective_price = combo_close_price if combo_close_price else close_cost
        pnl = round((net_credit - effective_price) * 100 * quantity, 2)
        print(f"  Entry credit:         {net_credit:.2f}")
        print(f"  Estimated P/L:       ${pnl:,.2f}")
    print()

    if not args.yes:
        confirm = input("Close position and cancel standing orders? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("Cancelled.")
            return

    close_oid = None
    combo_filled = False

    if has_combo_liquidity:
        print(f"Submitting combo close: BUY reverse combo LMT @ {combo_close_price:.2f} ...")
        close_body = {"orders": [{
            "conidex": reverse_conidex,
            "orderType": "LMT",
            "side": "BUY",
            "price": combo_close_price,
            "quantity": quantity,
            "tif": "DAY",
        }]}
        close_oid = submit_order(account_id, close_body)

        if close_oid:
            print(f"  Close order submitted: {close_oid}")
            time.sleep(5)
            try:
                status = get_order_status(close_oid)
                order_status = status.get("order_status", "")
                if order_status == "Filled":
                    combo_filled = True
                    print(f"  Combo close filled.")
                elif order_status == "Cancelled":
                    print(f"  Combo close was cancelled. Falling back to short legs ...")
                else:
                    time.sleep(5)
                    status = get_order_status(close_oid)
                    order_status = status.get("order_status", "")
                    if order_status == "Filled":
                        combo_filled = True
                        print(f"  Combo close filled.")
                    else:
                        print(f"  Combo close status: {order_status}. Cancelling and falling back to short legs ...")
                        try:
                            cancel_order(account_id, str(close_oid))
                        except Exception:
                            pass
            except Exception as e:
                print(f"  Error checking combo status: {e}. Cancelling and falling back to short legs ...")
                try:
                    cancel_order(account_id, str(close_oid))
                except Exception:
                    pass
        else:
            print("  Combo close failed. Falling back to short legs ...")
    else:
        print("  No combo liquidity (missing bid/ask). Closing short legs individually.")

    # Fallback: close short legs individually with LMT (they always have liquidity)
    if not combo_filled:
        short_conids = [l["conid"] for l in short_legs]
        print(f"\nRe-fetching fresh prices for short legs ...")
        fresh_snaps = get_market_snapshot(short_conids)
        print(f"Closing {len(short_legs)} short legs individually with LMT orders ...")
        for leg in short_legs:
            cid = leg["conid"]
            snap = fresh_snaps.get(cid, {})
            ask = snap.get("ask")
            if ask is None:
                label = leg.get("label", f"{leg.get('strike')} {leg.get('right')}")
                print(f"  SKIPPED {label} — no ask price available")
                continue
            lmt_price = ask
            label = leg.get("label", f"{leg.get('strike')} {leg.get('right')}")
            print(f"  BUY {quantity}x {label} LMT @ {lmt_price:.2f} ...")
            leg_body = {"orders": [{
                "conid": cid, "orderType": "LMT", "side": "BUY",
                "price": lmt_price, "quantity": quantity, "tif": "DAY",
            }]}
            leg_oid = submit_order(account_id, leg_body)
            if leg_oid:
                print(f"    Order {leg_oid}")
            else:
                print(f"    FAILED")
            time.sleep(0.5)
        long_labels = [l.get("label", f"{l.get('strike')}{l.get('right')}") for l in legs if l["action"] == "BUY"]
        if long_labels:
            print(f"\n  Long wings left to expire: {', '.join(long_labels)}")

    # Cancel related standing orders
    print("\nCancelling standing orders on same combo ...")
    live_orders = get_live_orders()
    cancelled = 0
    for order in live_orders:
        order_conidex = order.get("exchange", "")
        order_id = order.get("orderId")
        order_status = order.get("status", "")
        # Match orders on the same combo (exchange field contains the conidex for combos)
        if order_id and str(order_id) != str(close_oid) and order_status in ("PreSubmitted", "Submitted"):
            # Check if this order's legs match our combo legs
            order_legs = order_conidex.split(";;;")[-1] if ";;;" in order_conidex else ""
            our_legs = conidex.split(";;;")[-1]
            # Compare leg conids (ignore ratios)
            order_cids = set(p.rsplit("/", 1)[0] for p in order_legs.split(",") if "/" in p)
            our_cids = set(p.rsplit("/", 1)[0] for p in our_legs.split(",") if "/" in p)
            if order_cids == our_cids:
                try:
                    cancel_order(account_id, str(order_id))
                    print(f"  Cancelled order {order_id} ({order.get('orderDesc', '')[:60]})")
                    cancelled += 1
                except Exception as e:
                    print(f"  Failed to cancel {order_id}: {e}")

    if cancelled == 0:
        print("  No standing orders found to cancel.")

    print("\nDone.")


if __name__ == "__main__":
    main()
