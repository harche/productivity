#!/usr/bin/env python3
"""
IBKR Position Monitor.

Usage:
    python monitor.py
    python monitor.py --watch 30       # refresh every 30 seconds
    python monitor.py --symbol SPX     # filter by symbol
    python monitor.py --symbol SPX -g  # SPX positions with Greeks
"""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime
from typing import Optional

from ib_async import util
from ib_client import connect


def format_currency(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.2f}"


def format_pnl(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}${value:,.2f}"


def format_pct(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def display_positions(ib, symbol_filter: Optional[str] = None, show_greeks: bool = False) -> None:
    portfolio = ib.portfolio()

    if symbol_filter:
        filt = symbol_filter.upper()
        portfolio = [p for p in portfolio if filt in p.contract.symbol.upper()
                     or filt in str(p.contract.localSymbol).upper()]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'=' * 90}")
    print(f"  POSITIONS    {now}")
    print(f"{'=' * 90}")

    if not portfolio:
        print("  No open positions.")
        print(f"{'=' * 90}")
        return

    greeks_map = {}
    if show_greeks:
        opt_items = [p for p in portfolio if p.contract.secType == "OPT" and p.position != 0]
        if opt_items:
            tickers = ib.reqTickers(*[p.contract for p in opt_items])
            ib.sleep(2)
            for t in tickers:
                g = t.modelGreeks
                if g:
                    greeks_map[t.contract.conId] = {
                        "delta": g.delta, "gamma": g.gamma,
                        "theta": g.theta, "vega": g.vega, "iv": g.impliedVol,
                    }

    groups: dict[str, list] = {}
    for p in portfolio:
        asset = p.contract.secType or "OTHER"
        groups.setdefault(asset, []).append(p)

    total_mktval = 0.0
    total_unrealized = 0.0

    for asset_class in sorted(groups.keys()):
        group = groups[asset_class]
        label = {"OPT": "OPTIONS", "STK": "STOCKS", "FUT": "FUTURES",
                 "CASH": "CASH"}.get(asset_class, asset_class)
        print(f"\n  --- {label} ---")
        if show_greeks:
            print(f"  {'Description':<36} {'Pos':>6} {'Mkt Price':>10} {'Unrealized':>12} {'Delta':>7} {'Theta':>7} {'IV':>7}")
            print(f"  {'-' * 88}")
        else:
            print(f"  {'Description':<36} {'Pos':>6} {'Mkt Price':>10} {'Mkt Value':>12} {'Unrealized':>12} {'% P/L':>8}")
            print(f"  {'-' * 86}")

        for p in sorted(group, key=lambda x: x.contract.symbol):
            desc = p.contract.localSymbol or p.contract.symbol or "???"
            if len(desc) > 35:
                desc = desc[:32] + "..."

            price_str = f"{p.marketPrice:.2f}" if not util.isNan(p.marketPrice) else "N/A"

            pct = None
            if p.unrealizedPNL is not None and p.averageCost and p.position:
                cost_basis = p.averageCost * abs(p.position)
                if cost_basis != 0:
                    pct = (p.unrealizedPNL / cost_basis) * 100

            if show_greeks:
                g = greeks_map.get(p.contract.conId, {})
                delta_s = f"{g['delta']:.3f}" if g.get("delta") is not None else "N/A"
                theta_s = f"{g['theta']:.3f}" if g.get("theta") is not None else "N/A"
                iv_s = f"{g['iv']:.1%}" if g.get("iv") is not None else "N/A"
                print(f"  {desc:<36} {p.position:>6.0f} {price_str:>10} {format_pnl(p.unrealizedPNL):>12} {delta_s:>7} {theta_s:>7} {iv_s:>7}")
            else:
                print(f"  {desc:<36} {p.position:>6.0f} {price_str:>10} {format_currency(p.marketValue):>12} {format_pnl(p.unrealizedPNL):>12} {format_pct(pct):>8}")

            if p.marketValue is not None:
                total_mktval += p.marketValue
            if p.unrealizedPNL is not None:
                total_unrealized += p.unrealizedPNL

        print(f"  {'-' * 86}")

    print(f"\n  {'TOTAL':<36} {'':>6} {'':>10} {format_currency(total_mktval):>12} {format_pnl(total_unrealized):>12}")
    print(f"{'=' * 90}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor IBKR positions with live P/L.")
    parser.add_argument("--symbol", "-s", help="Filter positions by symbol")
    parser.add_argument("--watch", "-w", type=int, metavar="SECS", help="Refresh every N seconds")
    parser.add_argument("--greeks", "-g", action="store_true", help="Show Greeks for options")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    args = parser.parse_args()

    ib = connect(args.host, args.port)

    if args.watch:
        try:
            while True:
                os.system("clear" if os.name != "nt" else "cls")
                display_positions(ib, args.symbol, args.greeks)
                print(f"\n  Refreshing every {args.watch}s ... (Ctrl+C to stop)")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        display_positions(ib, args.symbol, args.greeks)

    ib.disconnect()


if __name__ == "__main__":
    main()
