#!/usr/bin/env python3
"""
SPX Box Spread builder via ib_async + ibkrbox pricing.

Uses ibkrbox for pure pricing math (get_limit), ib_async for gateway connection,
and ib_client for box_trade execution.

Usage:
    python box_spread.py --amount 10000 --months 3              # show (dry run)
    python box_spread.py --amount 10000 --months 3 --execute    # place order
    python box_spread.py --s1 5800 --s2 5900 --months 4         # manual strikes
    python box_spread.py --amount 10000 --months 3 --short      # borrow (short box)
    python box_spread.py --amount 10000 --months 3 --rate 4.5   # override rate
"""

from __future__ import annotations

import argparse
import sys

from ibkrbox.ibkrbox import get_limit  # pure math, no ib object needed

from ib_client import box_trade, connect, get_expiry, get_spx_price, get_strikes

MULTIPLIER = 100


def main() -> None:
    parser = argparse.ArgumentParser(description="SPX Box Spread")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    parser.add_argument("--acc", default="", help="Account ID")
    parser.add_argument("-a", "--amount", type=float, help="Dollar amount per contract")
    parser.add_argument("-m", "--months", type=int, help="Duration in months")
    parser.add_argument("-e", "--expiry", help="Expiry override (YYYYMMDD)")
    parser.add_argument("--s1", type=float, help="Lower strike")
    parser.add_argument("--s2", type=float, help="Upper strike")
    parser.add_argument("-r", "--rate", type=float, help="Interest rate override")
    parser.add_argument("-l", "--limit", type=float, help="Limit price override")
    parser.add_argument("-q", "--quantity", type=int, default=1)
    parser.add_argument("-t", "--timeout", type=int, default=20)
    parser.add_argument("--offset", type=float, help="Max offset for price sweep")
    parser.add_argument("--short", action="store_true", help="Short box (borrow)")
    parser.add_argument("--execute", action="store_true", help="Place order")

    args = parser.parse_args()

    if args.months is None and args.expiry is None:
        if args.limit is not None:
            parser.error("--limit requires --expiry (or use --months instead)")
        parser.error("Provide --months (or --expiry + --limit)")
    if args.amount is None and (args.s1 is None or args.s2 is None):
        parser.error("Provide --amount or both --s1 and --s2")

    print("Connecting to IB Gateway ...")
    ib = connect(args.host, args.port)

    expiry = args.expiry or get_expiry(ib, args.months)
    print(f"  Expiry: {expiry}")

    s1, s2 = args.s1, args.s2
    if s1 and not s2:
        s2 = s1 + int(args.amount / MULTIPLIER)
    if s2 and not s1:
        s1 = s2 - int(args.amount / MULTIPLIER)
    if not s1:
        s1, s2 = get_strikes(ib, args.amount)
    print(f"  Strikes: {s1} / {s2} (width: {s2 - s1})")

    limit = args.limit
    rate = args.rate
    if not limit:
        if not rate:
            rate = 4.3  # reasonable default; ibkrbox's get_rate is broken (Treasury CSV changed)
            print(f"  Rate: {rate:.2f}% (default — use --rate to override)")
        else:
            print(f"  Rate: {rate:.2f}%")
        limit = get_limit(expiry, rate, s1, s2)
    if args.short:
        limit = -abs(limit)
    print(f"  Limit: {limit:.2f}")

    max_price = limit + args.offset if args.offset else limit

    cost = abs(limit) * MULTIPLIER * args.quantity
    spread_value = (s2 - s1) * MULTIPLIER * args.quantity
    if args.short:
        print(f"\n  Borrow ${cost:,.0f} today, repay ${spread_value:,.0f} on {expiry}")
    else:
        print(f"\n  Lend ${cost:,.0f} today, receive ${spread_value:,.0f} on {expiry}")

    trade = box_trade(ib, expiry, s1, s2, limit,
                      quantity=args.quantity, short=args.short, acc=args.acc,
                      timeout=args.timeout, max_price=max_price,
                      execute=args.execute)

    if trade is not None:
        ib.sleep(5)
        print(f"\n  Filled: {trade.filled()} @ {trade.orderStatus.avgFillPrice:.2f}")

    ib.disconnect()
    print("Done.")


if __name__ == "__main__":
    main()
