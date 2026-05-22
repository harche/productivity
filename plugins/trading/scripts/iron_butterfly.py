#!/usr/bin/env python3
"""
Iron Butterfly / Iron Condor Strategy Builder for SPX via IBKR Client Portal Gateway API.

Builds ATM (butterfly) or OTM (condor) short-strike spreads, calculates
wing widths for the target risk/reward ratio, and outputs an order JSON
file that can be submitted via submit_order.py.

Usage:
    python iron_butterfly.py today                              # butterfly (ATM shorts)
    python iron_butterfly.py today --short-offset 0.3           # condor (shorts 0.3% OTM)
    python iron_butterfly.py today --short-offset 0.3 --submit  # condor, submit immediately
    python iron_butterfly.py tomorrow --quantity 2
    python iron_butterfly.py 2026-03-10 --output my_order.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta

from ibkr_client import (
    api_get,
    api_post,
    check_staleness,
    get_account_id as _client_get_account_id,
    get_market_snapshot,
    get_option_contract as _client_get_option_contract,
    initialize_session as _client_initialize_session,
    parse_price,
)

BASE_URL = "https://localhost:5000/v1/api"
SPX_CONID = 416904
STRIKE_INCREMENT = 5
REQUEST_DELAY = 0.15
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def round_to_strike(value: float) -> int:
    return int(round(value / STRIKE_INCREMENT) * STRIKE_INCREMENT)


def parse_expiry(expiry_arg: str) -> date:
    today = datetime.now().date()
    if expiry_arg.lower() == "today":
        return today
    elif expiry_arg.lower() == "tomorrow":
        return today + timedelta(days=1)
    else:
        return datetime.strptime(expiry_arg, "%Y-%m-%d").date()


def month_code(dt: date) -> str:
    return dt.strftime("%b%y").upper()


def maturity_str(dt: date) -> str:
    return dt.strftime("%Y%m%d")


# ---------------------------------------------------------------------------
# API interactions
# ---------------------------------------------------------------------------

def initialize_session() -> None:
    print("[1/9] Initializing session ...")
    _client_initialize_session()
    print("       Session authenticated.")
    time.sleep(REQUEST_DELAY)


def get_account_id() -> str:
    account_id = _client_get_account_id()
    print(f"       Account ID: {account_id}")
    time.sleep(REQUEST_DELAY)
    return account_id


def get_spx_price() -> float:
    print("[2/9] Fetching SPX price ...")
    data = api_get("/iserver/marketdata/history", params={
        "conid": SPX_CONID, "period": "1d", "bar": "1h",
    })
    bars = data.get("data", [])
    if not bars:
        raise RuntimeError("No historical data returned for SPX")
    price: float = bars[-1]["c"]
    print(f"       SPX: {price}")
    time.sleep(REQUEST_DELAY)
    return price


def get_option_contract_for_expiry(strike: float, right: str, expiry_date: date) -> dict:
    """Fetch a specific option contract via ibkr_client, deriving month/maturity from expiry_date."""
    month = month_code(expiry_date)
    maturity = maturity_str(expiry_date)
    return _client_get_option_contract(
        underlying_conid=SPX_CONID,
        strike=strike,
        right=right,
        month=month,
        maturity=maturity,
        exchange="SMART",
    )


def get_option_prices(conids: list[int]) -> dict[int, dict]:
    """Get bid/ask/last for multiple conids via ibkr_client.get_market_snapshot.

    Warns if any snapshot data is stale.
    Returns {conid: {"bid": float|None, "ask": float|None, "last": float|None}}.
    """
    snapshots = get_market_snapshot(conids)
    time.sleep(REQUEST_DELAY)

    stale = check_staleness(snapshots)
    if stale:
        print(f"  WARNING: Stale market data for conids: {stale}")

    results: dict[int, dict] = {}
    for cid, snap_data in snapshots.items():
        results[cid] = {
            "bid": snap_data.get("bid"),
            "ask": snap_data.get("ask"),
            "last": snap_data.get("last"),
        }
    return results


# ---------------------------------------------------------------------------
# Strategy construction
# ---------------------------------------------------------------------------

def build_strategy(spx_price: float, expiry_date: date, ratio: float = 2.0,
                   short_offset: float = 0.0) -> dict:
    is_condor = short_offset > 0
    if is_condor:
        print(f"[3/9] Finding OTM strikes ({short_offset}% offset) ...")
        offset_pts = spx_price * short_offset / 100.0
        lower = round_to_strike(spx_price - offset_pts)
        upper = round_to_strike(spx_price + offset_pts)
        print(f"       SPX={spx_price:.2f} -> Short Put @ {lower} (-{short_offset}%), Short Call @ {upper} (+{short_offset}%)")
    else:
        print("[3/9] Finding ATM strikes ...")
        lower = int(math.floor(spx_price / STRIKE_INCREMENT) * STRIKE_INCREMENT)
        upper = lower + STRIKE_INCREMENT
        print(f"       SPX={spx_price:.2f} -> Short Put @ {lower}, Short Call @ {upper}")

    strike_label = "OTM" if is_condor else "ATM"
    print(f"[4/9] Fetching {strike_label} option contracts ...")
    sp_contract = get_option_contract_for_expiry(lower, "P", expiry_date)
    sc_contract = get_option_contract_for_expiry(upper, "C", expiry_date)
    print(f"       Short Put  conid={sp_contract['conid']} ({sp_contract.get('tradingClass', '?')})")
    print(f"       Short Call conid={sc_contract['conid']} ({sc_contract.get('tradingClass', '?')})")

    print(f"[5/9] Fetching {strike_label} option prices ...")
    prices = get_option_prices([sp_contract["conid"], sc_contract["conid"]])
    sp_price = prices[sp_contract["conid"]]
    sc_price = prices[sc_contract["conid"]]
    print(f"       Short Put  bid={sp_price['bid']} ask={sp_price['ask']}")
    print(f"       Short Call bid={sc_price['bid']} ask={sc_price['ask']}")

    if sp_price["bid"] is None or sc_price["bid"] is None:
        raise RuntimeError("Could not get bid prices for short legs. Market may be closed.")

    print("[6/9] Calculating wing strikes ...")
    net_credit_shorts = sp_price["bid"] + sc_price["bid"]
    # wing_width = net_credit * (ratio + 1) to achieve max_loss = ratio * max_profit
    wing_width = round_to_strike((ratio + 1.0) * net_credit_shorts)
    if wing_width < STRIKE_INCREMENT:
        wing_width = STRIKE_INCREMENT

    lp_strike = lower - wing_width
    lc_strike = upper + wing_width
    print(f"       Net credit from shorts: {net_credit_shorts:.2f}")
    print(f"       Wing width: {wing_width} -> Long Put @ {lp_strike}, Long Call @ {lc_strike}")

    print("[7/9] Fetching wing option contracts ...")
    lp_contract = get_option_contract_for_expiry(lp_strike, "P", expiry_date)
    lc_contract = get_option_contract_for_expiry(lc_strike, "C", expiry_date)
    print(f"       Long Put  conid={lp_contract['conid']}")
    print(f"       Long Call conid={lc_contract['conid']}")

    print("[8/9] Fetching wing option prices ...")
    wing_prices = get_option_prices([lp_contract["conid"], lc_contract["conid"]])
    lp_price = wing_prices[lp_contract["conid"]]
    lc_price = wing_prices[lc_contract["conid"]]
    print(f"       Long Put  bid={lp_price['bid']} ask={lp_price['ask']}")
    print(f"       Long Call bid={lc_price['bid']} ask={lc_price['ask']}")

    if lp_price["ask"] is None or lc_price["ask"] is None:
        raise RuntimeError("Could not get ask prices for long legs. Market may be closed.")

    print("[9/9] Calculating final strategy ...")
    net_credit = net_credit_shorts - lp_price["ask"] - lc_price["ask"]
    max_profit = net_credit * 100
    max_loss = (wing_width - net_credit) * 100
    ratio = max_loss / max_profit if max_profit > 0 else float("inf")

    short_label = "OTM" if is_condor else "ATM"
    strategy_name = "iron_condor" if is_condor else "iron_butterfly"

    return {
        "strategy_name": strategy_name,
        "expiry": str(expiry_date),
        "spx_price": spx_price,
        "legs": [
            {"action": "BUY",  "strike": lp_strike, "right": "P", "conid": lp_contract["conid"],
             "bid": lp_price["bid"], "ask": lp_price["ask"], "label": "Long Put (wing)"},
            {"action": "SELL", "strike": lower,      "right": "P", "conid": sp_contract["conid"],
             "bid": sp_price["bid"], "ask": sp_price["ask"], "label": f"Short Put ({short_label})"},
            {"action": "SELL", "strike": upper,       "right": "C", "conid": sc_contract["conid"],
             "bid": sc_price["bid"], "ask": sc_price["ask"], "label": f"Short Call ({short_label})"},
            {"action": "BUY",  "strike": lc_strike,  "right": "C", "conid": lc_contract["conid"],
             "bid": lc_price["bid"], "ask": lc_price["ask"], "label": "Long Call (wing)"},
        ],
        "wing_width": wing_width,
        "net_credit": round(net_credit, 2),
        "max_profit": round(max_profit, 2),
        "max_loss": round(max_loss, 2),
        "ratio": round(ratio, 2),
        "lower_breakeven": round(lower - net_credit, 2),
        "upper_breakeven": round(upper + net_credit, 2),
    }


def display_strategy(strategy: dict, quantity: int) -> None:
    s = strategy
    title = "SPX IRON CONDOR" if s.get("strategy_name") == "iron_condor" else "SPX IRON BUTTERFLY"
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print(f"  Expiry:       {s['expiry']}")
    print(f"  SPX Price:    {s['spx_price']:.2f}")
    print(f"  Quantity:     {quantity}")
    print("-" * 70)
    print(f"  {'Leg':<22} {'Strike':>7} {'ConID':>12} {'Bid':>8} {'Ask':>8} {'Action':>6}")
    print("-" * 70)
    for leg in s["legs"]:
        bid_s = f"{leg['bid']:.2f}" if leg['bid'] is not None else "N/A"
        ask_s = f"{leg['ask']:.2f}" if leg['ask'] is not None else "N/A"
        print(f"  {leg['label']:<22} {leg['strike']:>7} {leg['conid']:>12} {bid_s:>8} {ask_s:>8} {leg['action']:>6}")
    print("-" * 70)
    print(f"  Wing Width:        {s['wing_width']} points")
    print(f"  Net Credit:        {s['net_credit']:.2f} per spread")
    print(f"  Max Profit:       ${s['max_profit'] * quantity:,.2f}")
    print(f"  Max Loss:         ${s['max_loss'] * quantity:,.2f}")
    print(f"  Risk/Reward:       {s['ratio']:.2f}x  (target ~2.0x)")
    print(f"  Lower Breakeven:   {s['lower_breakeven']:.2f}")
    print(f"  Upper Breakeven:   {s['upper_breakeven']:.2f}")
    print("=" * 70)


def build_order_json(account_id: str, strategy: dict, quantity: int) -> dict:
    """Build the order JSON that submit_order.py can consume."""
    legs = strategy["legs"]
    conidex_parts = []
    for leg in legs:
        ratio = 1 if leg["action"] == "BUY" else -1
        conidex_parts.append(f"{leg['conid']}/{ratio}")

    conidex = f"{SPX_CONID};;;{','.join(conidex_parts)}"
    limit_price = round(-strategy["net_credit"], 2)

    return {
        "account_id": account_id,
        "orders": [
            {
                "conidex": conidex,
                "orderType": "LMT",
                "side": "BUY",
                "price": limit_price,
                "tif": "DAY",
                "quantity": quantity,
            }
        ],
        "metadata": {
            "strategy": strategy.get("strategy_name", "iron_butterfly"),
            "symbol": "SPX",
            "expiry": strategy["expiry"],
            "net_credit": strategy["net_credit"],
            "max_profit": strategy["max_profit"],
            "max_loss": strategy["max_loss"],
            "ratio": strategy["ratio"],
            "legs": strategy["legs"],
        }
    }


def _submit_bracket(
    account_id: str, strategy: dict, quantity: int,
    bracket_profit: float, bracket_stop: float,
) -> None:
    """Submit entry order, then attach OCA-linked profit target + stop-loss.

    Submits the entry first, waits for fill, then submits profit target and
    stop-loss with a shared OCA group so one cancels the other on fill.
    """
    from ibkr_client import submit_order

    legs = strategy["legs"]
    conidex_parts = [f"{leg['conid']}/{1 if leg['action'] == 'BUY' else -1}" for leg in legs]
    conidex = f"{SPX_CONID};;;{','.join(conidex_parts)}"
    net_credit = strategy["net_credit"]
    oca_group = f"oca_SPX_{int(time.time())}"

    # Step 1: Submit entry order
    entry_price = round(-net_credit, 2)
    print(f"\n  [1/3] Submitting entry order: BUY combo LMT @ {entry_price} ...")
    entry_body = {"orders": [{
        "conidex": conidex, "orderType": "LMT", "side": "BUY",
        "price": entry_price, "quantity": quantity, "tif": "DAY",
    }]}
    entry_oid = submit_order(account_id, entry_body)
    if not entry_oid:
        print("  ERROR: Entry order failed.")
        sys.exit(1)

    # Wait for fill
    print(f"  Waiting for entry fill (order {entry_oid}) ...")
    from ibkr_client import get_order_status
    for _ in range(20):
        time.sleep(2)
        try:
            status = get_order_status(entry_oid)
            order_status = status.get("order_status", "").lower()
            fills = status.get("size_and_fills", "")
            if order_status == "filled":
                print(f"  Entry filled! ({fills})")
                break
            print(f"  ... {order_status} ({fills})")
        except Exception:
            pass
    else:
        print("  Entry not filled after 40s. Submitting exit orders anyway.")

    # Step 2: Submit profit target with OCA group
    close_price = round(net_credit - (bracket_profit / 100.0 / quantity), 2)
    profit_price = round(-close_price, 2)
    print(f"  [2/3] Submitting profit target: SELL combo LMT @ {profit_price} (OCA: {oca_group}) ...")
    profit_body = {"orders": [{
        "conidex": conidex, "orderType": "LMT", "side": "SELL",
        "price": profit_price, "quantity": quantity, "tif": "DAY",
        "ocaGroup": oca_group, "ocaType": 1,
    }]}
    profit_oid = submit_order(account_id, profit_body)

    # Step 3: Submit stop-loss with same OCA group (STP LMT on combo)
    stop_price = round(net_credit + (bracket_stop / 100.0 / quantity), 2)
    stop_limit = round(stop_price + 2, 2)
    print(f"  [3/3] Submitting stop-loss: SELL combo STP LMT stop={-stop_price} limit={-stop_limit} (OCA: {oca_group}) ...")
    stop_body = {"orders": [{
        "conidex": conidex, "orderType": "STP LMT", "side": "SELL",
        "auxPrice": round(-stop_price, 2), "price": round(-stop_limit, 2),
        "quantity": quantity, "tif": "DAY",
        "ocaGroup": oca_group, "ocaType": 1,
    }]}
    stop_oid = submit_order(account_id, stop_body)

    print(f"\n  Bracket submitted:")
    print(f"    Entry:         Order {entry_oid}")
    print(f"    Profit target: Order {profit_oid or 'FAILED'} (${bracket_profit:,.0f})")
    print(f"    Stop loss:     Order {stop_oid or 'FAILED'} (${bracket_stop:,.0f})")
    print(f"    OCA Group:     {oca_group}")
    if profit_oid and stop_oid:
        print(f"  When profit target or stop-loss fills, the other is automatically cancelled.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build an SPX Iron Butterfly or Iron Condor order and save to JSON for submission."
    )
    parser.add_argument("expiry", help='"today", "tomorrow", or YYYY-MM-DD')
    parser.add_argument("--quantity", type=int, default=1, help="Number of contracts (default: 1)")
    parser.add_argument("--ratio", type=float, default=2.0,
                        help="Target max_loss/max_profit ratio (default: 2.0). Lower = tighter wings.")
    parser.add_argument("--short-offset", type=float, default=0.0,
                        help="Place short strikes N%% OTM from SPX price (default: 0 = ATM butterfly). "
                             "E.g., --short-offset 0.3 builds an iron condor with shorts 0.3%% OTM.")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON file path (default: iron_butterfly_<date>.json or iron_condor_<date>.json)")
    parser.add_argument("--submit", action="store_true",
                        help="Immediately submit the order via submit_order.py after building")
    parser.add_argument("--bracket", nargs=2, type=float, metavar=("PROFIT", "STOP_LOSS"),
                        help="Submit entry + bracket orders: profit target and stop-loss in dollars (e.g., --bracket 2000 4000). Implies --submit.")
    args = parser.parse_args()

    expiry_date = parse_expiry(args.expiry)
    is_condor = args.short_offset > 0
    default_prefix = "iron_condor" if is_condor else "iron_butterfly"
    output_file = args.output or f"{default_prefix}_{expiry_date}.json"
    strategy_type = "Iron Condor" if is_condor else "Iron Butterfly"
    print(f"Strategy:      {strategy_type}" + (f" (shorts {args.short_offset}% OTM)" if is_condor else ""))
    print(f"Target expiry: {expiry_date} ({expiry_date.strftime('%A')})")
    print(f"Quantity:      {args.quantity}")
    print(f"Output:        {output_file}")
    print()

    initialize_session()
    account_id = get_account_id()
    spx_price = get_spx_price()
    strategy = build_strategy(spx_price, expiry_date, ratio=args.ratio,
                              short_offset=args.short_offset)
    display_strategy(strategy, args.quantity)

    order_json = build_order_json(account_id, strategy, args.quantity)

    with open(output_file, "w") as f:
        json.dump(order_json, f, indent=2)
    print(f"\nOrder saved to: {output_file}")

    if args.bracket:
        bracket_profit = args.bracket[0]
        bracket_stop = args.bracket[1]
        print(f"\n  Bracket mode: entry + profit target (${bracket_profit:,.0f}) + stop-loss (${bracket_stop:,.0f})")
        if args.submit:
            _submit_bracket(account_id, strategy, args.quantity, bracket_profit, bracket_stop)
        else:
            print("  [DRY RUN] Bracket order not submitted. Add --submit to execute.")
    elif args.submit:
        submit_script = os.path.join(SCRIPT_DIR, "submit_order.py")
        print("\nSubmitting order ...")
        result = subprocess.run([sys.executable, submit_script, output_file, "-y"])
        sys.exit(result.returncode)
    else:
        print(f"To submit:  python3 {os.path.join(SCRIPT_DIR, 'submit_order.py')} {output_file}")


if __name__ == "__main__":
    main()
