#!/usr/bin/env python3
"""
Close an IBKR combo position.

Usage:
    python close_position.py --strikes 7410P,7465P,7510C,7565C
    python close_position.py --strikes 7450P,7475P,7520C,7545C -y
    python close_position.py iron_butterfly_2026-03-12.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from ib_async import Contract, LimitOrder, util
from ib_client import connect

from ib_client import build_combo, round_to_tick


def parse_strikes(strikes_str: str) -> list[tuple[int, str]]:
    result = []
    for s in strikes_str.split(","):
        s = s.strip().upper()
        m = re.match(r"^(\d+)([PC])$", s)
        if not m:
            sys.exit(f"ERROR: Invalid strike format '{s}'.")
        result.append((int(m.group(1)), m.group(2)))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Close an IBKR combo position.")
    parser.add_argument("file", nargs="?", default=None)
    parser.add_argument("--strikes", type=str)
    parser.add_argument("-y", "--yes", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    args = parser.parse_args()

    if not args.file and not args.strikes:
        parser.error("Either provide a JSON file or use --strikes.")

    ib = connect(args.host, args.port)

    if args.strikes:
        strike_list = parse_strikes(args.strikes)
        positions = ib.positions()
        matched = []
        for target_strike, target_right in strike_list:
            found = False
            for pos in positions:
                c = pos.contract
                if c.symbol == "SPX" and c.secType == "OPT" and c.strike == target_strike and c.right == target_right and pos.position != 0:
                    matched.append({
                        "conid": c.conId, "contract": c, "strike": target_strike,
                        "right": target_right,
                        "action": "BUY" if pos.position > 0 else "SELL",
                        "position": pos.position,
                        "label": f"{'Long' if pos.position > 0 else 'Short'} {'Put' if target_right == 'P' else 'Call'} ({target_strike})",
                    })
                    found = True
                    break
            if not found:
                sys.exit(f"ERROR: No open SPX position for {target_strike}{target_right}")

        quantity = int(min(abs(m["position"]) for m in matched))
        print(f"Found {len(matched)} legs, quantity={quantity}")
    else:
        with open(args.file) as f:
            meta = json.load(f).get("metadata", {})
        legs = meta.get("legs", [])
        if not legs:
            sys.exit("ERROR: No leg data in metadata.")
        matched = [{"conid": l["conid"], "action": l["action"],
                     "label": l.get("label", f"{l['action']} {l.get('strike')}{l.get('right')}")}
                    for l in legs]
        quantity = 1
        print(f"Close: {meta.get('strategy', 'combo')} {meta.get('expiry', '')}")

    # Build reverse combo
    bag = build_combo("SPX", [
        (Contract(conId=m["conid"], exchange="SMART"),
         "SELL" if m["action"] == "BUY" else "BUY")
        for m in matched
    ])

    # Get combo price
    tickers = ib.reqTickers(bag)
    ib.sleep(2)
    bid = ask = None
    if tickers:
        t = tickers[0]
        bid = t.bid if not util.isNan(t.bid) else None
        ask = t.ask if not util.isNan(t.ask) else None
        ib.cancelMktData(bag)

    print(f"  Combo bid={bid}  ask={ask}")

    if ask is not None:
        close_price = round_to_tick(ask)
    elif bid is not None:
        close_price = round_to_tick(bid)
    else:
        sys.exit("  No combo price available.")

    for m in matched:
        close_action = "SELL" if m["action"] == "BUY" else "BUY"
        print(f"    {close_action} {m['label']}")

    if not args.yes:
        confirm = input(f"\nClose @ {close_price}? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("Cancelled.")
            ib.disconnect()
            return

    trade = ib.placeOrder(bag, LimitOrder("BUY", quantity, close_price))
    ib.sleep(5)
    print(f"  Status: {trade.orderStatus.status}")

    # Cancel standing orders on same combo
    our_conids = {m["conid"] for m in matched}
    for t in ib.openTrades():
        if t.contract.secType == "BAG" and t.contract.comboLegs:
            if {leg.conId for leg in t.contract.comboLegs} == our_conids:
                ib.cancelOrder(t.order)
                print(f"  Cancelled standing order {t.order.orderId}")

    print("Done.")
    ib.disconnect()


if __name__ == "__main__":
    main()
