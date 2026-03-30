#!/usr/bin/env python3
"""
IBKR Position Monitor via Client Portal Gateway API.

Displays all open positions with live P/L, market value, and price data.

Usage:
    python monitor.py
    python monitor.py --watch 30       # refresh every 30 seconds
    python monitor.py --symbol SPX     # filter by symbol
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from typing import Optional

from ibkr_client import api_get, get_account_id, get_market_snapshot, get_positions, initialize_session, parse_price


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


def _fetch_all_positions(account_id: str, symbol_filter: Optional[str] = None) -> list[dict]:
    """Fetch all position pages, optionally filtering by symbol."""
    positions: list[dict] = []
    page = 0
    while True:
        page_data = get_positions(account_id, page=page)
        if not page_data:
            break
        positions.extend(page_data)
        page += 1
        if len(page_data) < 30:
            break
        time.sleep(0.15)

    if symbol_filter:
        filt = symbol_filter.upper()
        positions = [p for p in positions if filt in (p.get("ticker", "") or "").upper()
                     or filt in (p.get("contractDesc", "") or "").upper()]

    return positions


def _refresh_prices(positions: list[dict]) -> None:
    """Fetch live market data snapshots and update prices for single-leg positions.

    The /portfolio/positions endpoint returns cached prices that can be minutes
    old. This function fetches fresh data from /iserver/marketdata/snapshot and
    updates mktPrice/mktValue/unrealizedPnl in-place.

    Only single-leg positions (stocks, individual options) are refreshed.
    Combo/multi-leg positions (e.g. iron butterflies) are left unchanged
    because individual leg prices don't reflect the actual combo market —
    IBKR's portfolio P/L is more accurate for those.
    """
    # Only refresh single-leg positions (STK, individual OPT, FUT, etc.)
    # Detect combo legs: if multiple positions share the same ticker and
    # asset class OPT with the same expiry, they're likely part of a combo.
    # A simpler heuristic: count how many OPT positions exist per ticker.
    # If a ticker has >1 OPT position with non-zero qty, treat all its
    # options as combo legs and skip them.
    from collections import Counter
    opt_ticker_counts: Counter[str] = Counter()
    for p in positions:
        if p.get("assetClass") == "OPT" and p.get("position", 0) != 0:
            ticker = p.get("ticker", "")
            opt_ticker_counts[ticker] += 1

    combo_tickers = {t for t, c in opt_ticker_counts.items() if c > 1}

    active = []
    for p in positions:
        if p.get("position", 0) == 0 or not p.get("conid"):
            continue
        # Skip combo legs
        if p.get("assetClass") == "OPT" and p.get("ticker", "") in combo_tickers:
            continue
        active.append(p)

    if not active:
        return

    conids = [p["conid"] for p in active]
    conid_str = ",".join(str(c) for c in conids)

    # Prime the snapshot subscription
    api_get("/iserver/marketdata/snapshot", params={"conids": conid_str, "fields": "31,84,86"})
    time.sleep(2.5)
    # Read fresh data
    data = api_get("/iserver/marketdata/snapshot", params={"conids": conid_str, "fields": "31,84,86"})

    snapshots: dict[int, dict] = {}
    for snap in (data if isinstance(data, list) else [data]):
        cid = snap.get("conid")
        snapshots[cid] = {
            "bid": parse_price(snap.get("84")),
            "ask": parse_price(snap.get("86")),
            "last": parse_price(snap.get("31")),
        }

    for p in active:
        cid = p.get("conid")
        snap = snapshots.get(cid)
        if not snap:
            continue

        last = snap.get("last")
        bid = snap.get("bid")
        ask = snap.get("ask")

        if last is not None:
            fresh_price = last
        elif bid is not None and ask is not None:
            fresh_price = (bid + ask) / 2
        else:
            continue

        pos = p.get("position", 0)
        multiplier = p.get("multiplier")
        if multiplier is None:
            multiplier = 1.0
        elif isinstance(multiplier, str):
            try:
                multiplier = float(multiplier)
            except ValueError:
                multiplier = 1.0
        else:
            multiplier = float(multiplier)
        avg_cost = p.get("avgCost", 0)

        p["mktPrice"] = fresh_price
        p["mktValue"] = fresh_price * pos * multiplier
        p["unrealizedPnl"] = (fresh_price * pos * multiplier) - (avg_cost * pos)


def _fetch_greeks(positions: list[dict]) -> dict[int, dict]:
    """Fetch Greeks for option positions via market data snapshot."""
    opt_conids = [
        p.get("conid") for p in positions
        if p.get("assetClass") == "OPT" and p.get("conid") and p.get("position", 0) != 0
    ]
    if not opt_conids:
        return {}

    # Fields: 7308=delta, 7309=gamma, 7310=theta, 7311=vega, 7633=IV
    snapshots = get_market_snapshot(opt_conids, fields="7308,7309,7310,7311,7633")

    greeks: dict[int, dict] = {}
    for cid, snap in snapshots.items():
        greeks[cid] = {
            "delta": parse_price(snap.get("bid")),   # field mapping differs in snapshot
            "gamma": parse_price(snap.get("ask")),
            "theta": parse_price(snap.get("last")),
            "vega": None,
            "iv": None,
        }

    # Re-fetch with raw field access since get_market_snapshot maps to bid/ask/last
    # We need the raw fields directly
    conid_str = ",".join(str(c) for c in opt_conids)
    from ibkr_client import api_get
    data = api_get("/iserver/marketdata/snapshot", params={"conids": conid_str, "fields": "7308,7309,7310,7311,7633"})

    for snap in (data if isinstance(data, list) else [data]):
        cid = snap.get("conid")
        greeks[cid] = {
            "delta": parse_price(snap.get("7308")),
            "gamma": parse_price(snap.get("7309")),
            "theta": parse_price(snap.get("7310")),
            "vega": parse_price(snap.get("7311")),
            "iv": snap.get("7633"),
        }

    return greeks


def display_positions(positions: list[dict], account_id: str, greeks: Optional[dict[int, dict]] = None) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'=' * 90}")
    print(f"  POSITIONS — {account_id}    {now}")
    print(f"{'=' * 90}")

    if not positions:
        print("  No open positions.")
        print(f"{'=' * 90}")
        return

    # Group by asset class
    groups: dict[str, list[dict]] = {}
    for p in positions:
        asset = p.get("assetClass", "OTHER")
        groups.setdefault(asset, []).append(p)

    total_mktval: float = 0
    total_unrealized: float = 0

    for asset_class in sorted(groups.keys()):
        group = groups[asset_class]
        label = {"OPT": "OPTIONS", "STK": "STOCKS", "FUT": "FUTURES",
                 "CASH": "CASH", "WAR": "WARRANTS", "BOND": "BONDS"}.get(asset_class, asset_class)
        print(f"\n  --- {label} ---")
        if greeks:
            print(f"  {'Description':<36} {'Pos':>6} {'Mkt Price':>10} {'Unrealized':>12} {'Delta':>7} {'Theta':>7} {'IV':>7}")
            print(f"  {'-' * 88}")
        else:
            print(f"  {'Description':<36} {'Pos':>6} {'Mkt Price':>10} {'Mkt Value':>12} {'Unrealized':>12} {'% P/L':>8}")
            print(f"  {'-' * 86}")

        for p in sorted(group, key=lambda x: x.get("ticker", "")):
            desc: str = p.get("contractDesc", p.get("ticker", "???"))
            if len(desc) > 35:
                desc = desc[:32] + "..."
            pos: float = p.get("position", 0)
            mkt_price: Optional[float] = p.get("mktPrice", None)
            mkt_value: Optional[float] = p.get("mktValue", None)
            unrealized: Optional[float] = p.get("unrealizedPnl", None)
            avg_cost: Optional[float] = p.get("avgCost", None)

            pct: Optional[float] = None
            if unrealized is not None and avg_cost is not None and pos != 0:
                cost_basis = avg_cost * abs(pos)
                if cost_basis != 0:
                    pct = (unrealized / cost_basis) * 100

            price_str = f"{mkt_price:.2f}" if mkt_price is not None else "N/A"
            if greeks:
                cid = p.get("conid")
                g = greeks.get(cid, {}) if cid else {}
                delta_s = f"{g['delta']:.3f}" if g.get("delta") is not None else "N/A"
                theta_s = f"{g['theta']:.3f}" if g.get("theta") is not None else "N/A"
                iv_s = str(g.get("iv", "N/A"))
                print(f"  {desc:<36} {pos:>6.0f} {price_str:>10} {format_pnl(unrealized):>12} {delta_s:>7} {theta_s:>7} {iv_s:>7}")
            else:
                print(f"  {desc:<36} {pos:>6.0f} {price_str:>10} {format_currency(mkt_value):>12} {format_pnl(unrealized):>12} {format_pct(pct):>8}")

            if mkt_value is not None:
                total_mktval += mkt_value
            if unrealized is not None:
                total_unrealized += unrealized

        print(f"  {'-' * 86}")

    print(f"\n  {'TOTAL':<36} {'':>6} {'':>10} {format_currency(total_mktval):>12} {format_pnl(total_unrealized):>12}")
    print(f"{'=' * 90}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor IBKR positions with live P/L.")
    parser.add_argument("--symbol", "-s", help="Filter positions by symbol (e.g., SPX, AAPL)")
    parser.add_argument("--watch", "-w", type=int, metavar="SECS",
                        help="Refresh every N seconds (default: one-shot)")
    parser.add_argument("--greeks", "-g", action="store_true",
                        help="Show Greeks (delta, theta, IV) for option positions")
    args = parser.parse_args()

    initialize_session()
    account_id: str = get_account_id()

    if args.watch:
        try:
            while True:
                os.system("clear" if os.name != "nt" else "cls")
                positions = _fetch_all_positions(account_id, args.symbol)
                _refresh_prices(positions)
                greeks = _fetch_greeks(positions) if args.greeks else None
                display_positions(positions, account_id, greeks)
                print(f"\n  Refreshing every {args.watch}s ... (Ctrl+C to stop)")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        positions = _fetch_all_positions(account_id, args.symbol)
        _refresh_prices(positions)
        greeks = _fetch_greeks(positions) if args.greeks else None
        display_positions(positions, account_id, greeks)


if __name__ == "__main__":
    main()
