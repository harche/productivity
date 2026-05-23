#!/usr/bin/env python3
"""
Iron Butterfly / Iron Condor Strategy Builder for SPX via ib_async.

Builds ATM (butterfly) or OTM (condor) short-strike spreads, calculates
wing widths for the target risk/reward ratio, and submits combo orders
natively via IB Gateway.

Usage:
    python iron_butterfly.py today                              # butterfly (ATM shorts)
    python iron_butterfly.py today --short-offset 0.3           # condor (shorts 0.3% OTM)
    python iron_butterfly.py today --short-offset 0.3 --submit  # condor, submit immediately
    python iron_butterfly.py tomorrow --quantity 2
    python iron_butterfly.py today --strategy 3 --submit        # condor, 60% TP, submit
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import date, datetime, timedelta

from ib_async import ComboLeg, Contract, Index, LimitOrder, Option, Order, util
from ibkrbox.ibkrbox import get_last

from ib_client import build_combo, connect, find_option_by_delta, round_to_tick, sweep_fill

STRIKE_INCREMENT = 5
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

STRATEGIES = {
    1: {"name": "Iron Butterfly — Hold to Expiry",    "short_offset": 0.0, "ratio": 2.0, "profit_target_pct": None},
    2: {"name": "Iron Butterfly — 60% Profit Target", "short_offset": 0.0, "ratio": 2.0, "profit_target_pct": 0.6},
    3: {"name": "Iron Condor — 60% Profit Target",    "short_offset": 0.3, "ratio": 2.0, "profit_target_pct": 0.6},
    4: {"name": "Iron Condor — Hold to Expiry",        "short_offset": 0.3, "ratio": 2.0, "profit_target_pct": None},
}


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


def find_best_trading_class(ib, expiry_str: str) -> str:
    """Find the trading class (SPXW for weeklies, SPX for monthlies) available for an expiry."""
    spx = ib.qualifyContracts(Index("SPX", "CBOE"))[0]
    chains = ib.reqSecDefOptParams(spx.symbol, "", spx.secType, spx.conId)
    for chain in chains:
        if chain.exchange == "SMART" and chain.tradingClass == "SPXW" and expiry_str in chain.expirations:
            return "SPXW"
    for chain in chains:
        if chain.exchange == "SMART" and chain.tradingClass == "SPX" and expiry_str in chain.expirations:
            return "SPX"
    return "SPXW"


def qualify_leg(ib, strike: float, right: str, expiry_str: str, trading_class: str) -> Option:
    """Qualify a single option leg."""
    opt = Option("SPX", expiry_str, strike, right, "SMART", tradingClass=trading_class)
    qualified = ib.qualifyContracts(opt)
    if not qualified or qualified[0].conId == 0:
        raise RuntimeError(f"Could not qualify: SPX {expiry_str} {strike}{right} ({trading_class})")
    return qualified[0]


def get_leg_prices(ib, contracts: list) -> dict:
    """Get bid/ask for a list of contracts via reqTickers."""
    tickers = ib.reqTickers(*contracts)
    ib.sleep(2)
    prices = {}
    for t in tickers:
        prices[t.contract.conId] = {
            "bid": t.bid if not util.isNan(t.bid) else None,
            "ask": t.ask if not util.isNan(t.ask) else None,
            "last": t.last if not util.isNan(t.last) else None,
        }
    for t in tickers:
        ib.cancelMktData(t.contract)
    return prices


def build_strategy(ib, spx_price: float, expiry_date: date,
                   ratio: float = 2.0, short_offset: float = 0.0) -> dict:
    expiry_str = expiry_date.strftime("%Y%m%d")
    is_condor = short_offset > 0

    if is_condor:
        print(f"[2/5] Finding OTM strikes ({short_offset}% offset) ...")
        offset_pts = spx_price * short_offset / 100.0
        lower = round_to_strike(spx_price - offset_pts)
        upper = round_to_strike(spx_price + offset_pts)
        print(f"       SPX={spx_price:.2f} -> Short Put @ {lower}, Short Call @ {upper}")
    else:
        print("[2/5] Finding ATM strikes ...")
        lower = int(math.floor(spx_price / STRIKE_INCREMENT) * STRIKE_INCREMENT)
        upper = lower + STRIKE_INCREMENT
        print(f"       SPX={spx_price:.2f} -> Short Put @ {lower}, Short Call @ {upper}")

    trading_class = find_best_trading_class(ib, expiry_str)
    print(f"       Trading class: {trading_class}")

    print("[3/5] Qualifying short legs + fetching prices ...")
    sp_contract = qualify_leg(ib, lower, "P", expiry_str, trading_class)
    sc_contract = qualify_leg(ib, upper, "C", expiry_str, trading_class)
    print(f"       Short Put  conid={sp_contract.conId}")
    print(f"       Short Call conid={sc_contract.conId}")

    prices = get_leg_prices(ib, [sp_contract, sc_contract])
    sp_price = prices[sp_contract.conId]
    sc_price = prices[sc_contract.conId]
    print(f"       Short Put  bid={sp_price['bid']} ask={sp_price['ask']}")
    print(f"       Short Call bid={sc_price['bid']} ask={sc_price['ask']}")

    if sp_price["bid"] is None or sc_price["bid"] is None:
        raise RuntimeError("Could not get bid prices for short legs. Market may be closed.")

    net_credit_shorts = sp_price["bid"] + sc_price["bid"]
    print(f"       Net credit from shorts: {net_credit_shorts:.2f}")

    print("[4/5] Calculating wing strikes + fetching prices ...")
    wing_width = round_to_strike((ratio + 1.0) * net_credit_shorts)
    if wing_width < STRIKE_INCREMENT:
        wing_width = STRIKE_INCREMENT

    for iteration in range(3):
        lp_strike = lower - wing_width
        lc_strike = upper + wing_width
        if iteration == 0:
            print(f"       Wing width: {wing_width} -> Long Put @ {lp_strike}, Long Call @ {lc_strike}")

        lp_contract = qualify_leg(ib, lp_strike, "P", expiry_str, trading_class)
        lc_contract = qualify_leg(ib, lc_strike, "C", expiry_str, trading_class)

        wing_prices = get_leg_prices(ib, [lp_contract, lc_contract])
        lp_price = wing_prices[lp_contract.conId]
        lc_price = wing_prices[lc_contract.conId]

        if lp_price["ask"] is None or lc_price["ask"] is None:
            raise RuntimeError("Could not get ask prices for wing legs. Market may be closed.")

        net_credit = net_credit_shorts - lp_price["ask"] - lc_price["ask"]
        target_wing_width = round_to_strike((ratio + 1.0) * net_credit)
        if target_wing_width < STRIKE_INCREMENT:
            target_wing_width = STRIKE_INCREMENT
        if target_wing_width == wing_width:
            break
        wing_width = target_wing_width
        print(f"       Adjusted wing width: {wing_width}")

    print(f"       Long Put  conid={lp_contract.conId} bid={lp_price['bid']} ask={lp_price['ask']}")
    print(f"       Long Call conid={lc_contract.conId} bid={lc_price['bid']} ask={lc_price['ask']}")

    print("[5/5] Final strategy ...")
    net_credit = net_credit_shorts - lp_price["ask"] - lc_price["ask"]
    max_profit = net_credit * 100
    max_loss = (wing_width - net_credit) * 100
    final_ratio = max_loss / max_profit if max_profit > 0 else float("inf")

    short_label = "OTM" if is_condor else "ATM"
    strategy_name = "iron_condor" if is_condor else "iron_butterfly"

    return {
        "strategy_name": strategy_name,
        "expiry": str(expiry_date),
        "expiry_str": expiry_str,
        "trading_class": trading_class,
        "spx_price": spx_price,
        "legs": [
            {"action": "BUY",  "strike": lp_strike, "right": "P", "conid": lp_contract.conId,
             "contract": lp_contract, "bid": lp_price["bid"], "ask": lp_price["ask"], "label": "Long Put (wing)"},
            {"action": "SELL", "strike": lower,      "right": "P", "conid": sp_contract.conId,
             "contract": sp_contract, "bid": sp_price["bid"], "ask": sp_price["ask"], "label": f"Short Put ({short_label})"},
            {"action": "SELL", "strike": upper,       "right": "C", "conid": sc_contract.conId,
             "contract": sc_contract, "bid": sc_price["bid"], "ask": sc_price["ask"], "label": f"Short Call ({short_label})"},
            {"action": "BUY",  "strike": lc_strike,  "right": "C", "conid": lc_contract.conId,
             "contract": lc_contract, "bid": lc_price["bid"], "ask": lc_price["ask"], "label": "Long Call (wing)"},
        ],
        "wing_width": wing_width,
        "net_credit": round(net_credit, 2),
        "max_profit": round(max_profit, 2),
        "max_loss": round(max_loss, 2),
        "ratio": round(final_ratio, 2),
        "lower_breakeven": round(lower - net_credit, 2),
        "upper_breakeven": round(upper + net_credit, 2),
    }


def display_strategy(strategy: dict, quantity: int, strategy_num: int | None = None) -> None:
    s = strategy
    title = "SPX IRON CONDOR" if s.get("strategy_name") == "iron_condor" else "SPX IRON BUTTERFLY"
    if strategy_num is not None:
        title += f"  [Strategy {strategy_num}]"
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
    print(f"  Risk/Reward:       {s['ratio']:.2f}x")
    print(f"  Lower Breakeven:   {s['lower_breakeven']:.2f}")
    print(f"  Upper Breakeven:   {s['upper_breakeven']:.2f}")
    print("=" * 70)


def build_combo_contract(strategy: dict) -> Contract:
    """Build a BAG contract from strategy legs."""
    return build_combo("SPX", [
        (Contract(conId=leg["conid"], exchange="SMART"), leg["action"])
        for leg in strategy["legs"]
    ])


def get_combo_price(ib, bag: Contract) -> tuple[float | None, float | None]:
    """Get bid/ask for a combo contract."""
    tickers = ib.reqTickers(bag)
    ib.sleep(2)
    if tickers:
        t = tickers[0]
        bid = t.bid if not util.isNan(t.bid) else None
        ask = t.ask if not util.isNan(t.ask) else None
        ib.cancelMktData(bag)
        return bid, ask
    return None, None


def wait_for_fill(ib, trade, timeout: int = 40) -> bool:
    """Wait for trade to fill. Returns True if filled."""
    import time
    start = time.time()
    while time.time() - start < timeout:
        ib.sleep(2)
        if trade.isDone():
            return trade.orderStatus.status == "Filled"
        print(f"  ... {trade.orderStatus.status} (filled: {trade.filled()})")
    return False


def submit_with_bracket(ib, bag: Contract, strategy: dict,
                        quantity: int, profit_target_pct: float | None = None,
                        bracket_profit: float | None = None, bracket_stop: float | None = None,
                        account: str = "") -> None:
    """Submit entry + bracket orders using parent/child pattern from 0dte-trader."""
    net_credit = strategy["net_credit"]

    combo_bid, combo_ask = get_combo_price(ib, bag)
    if combo_ask is not None:
        entry_price = round_to_tick(combo_ask)
        print(f"\n  Combo bid={combo_bid}  ask={combo_ask}  (using ask as entry)")
    elif combo_bid is not None:
        entry_price = round_to_tick(combo_bid)
        print(f"\n  Combo bid={combo_bid}  (using bid as entry)")
    else:
        entry_price = round_to_tick(-net_credit)
        print(f"\n  Combo price unavailable, using leg-derived: {entry_price}")

    entry_order = LimitOrder("BUY", quantity, entry_price, account=account)
    entry_order.transmit = False
    entry_trade = ib.placeOrder(bag, entry_order)
    print(f"  Entry order placed: {entry_order.orderId}")

    if profit_target_pct is not None:
        close_credit = round(net_credit * (1.0 - profit_target_pct), 2)
        profit_price = round_to_tick(-close_credit)
        profit_order = LimitOrder("SELL", quantity, profit_price, account=account)
        profit_order.parentId = entry_order.orderId
        profit_order.transmit = True
        ib.placeOrder(bag, profit_order)
        target_dollars = net_credit * profit_target_pct * quantity * 100
        print(f"  Profit target: SELL @ {profit_price} ({profit_target_pct:.0%} = ${target_dollars:,.0f})")

    elif bracket_profit is not None and bracket_stop is not None:
        close_price = round(net_credit - (bracket_profit / 100.0 / quantity), 2)
        profit_price = round_to_tick(-close_price)
        profit_order = LimitOrder("SELL", quantity, profit_price, account=account)
        profit_order.parentId = entry_order.orderId
        profit_order.transmit = False
        ib.placeOrder(bag, profit_order)
        print(f"  Profit target: SELL @ {profit_price} (${bracket_profit:,.0f})")

        stop_price = round(net_credit + (bracket_stop / 100.0 / quantity), 2)
        stop_limit = round_to_tick(-(stop_price + 2))
        stop_order = Order()
        stop_order.action = "SELL"
        stop_order.totalQuantity = quantity
        stop_order.orderType = "STP LMT"
        stop_order.auxPrice = round_to_tick(-stop_price)
        stop_order.lmtPrice = stop_limit
        stop_order.parentId = entry_order.orderId
        stop_order.transmit = True
        if account:
            stop_order.account = account
        ib.placeOrder(bag, stop_order)
        print(f"  Stop loss: STP LMT stop={-stop_price:.2f} limit={stop_limit:.2f} (${bracket_stop:,.0f})")
    else:
        entry_order.transmit = True
        ib.placeOrder(bag, entry_order)

    print(f"\n  Orders submitted. Waiting for entry fill ...")
    filled = wait_for_fill(ib, entry_trade)
    if filled:
        print(f"  Entry filled @ {entry_trade.orderStatus.avgFillPrice:.2f}")
    else:
        print(f"  Entry not filled after timeout. Orders remain active.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build an SPX Iron Butterfly or Iron Condor via IB Gateway."
    )
    parser.add_argument("expiry", help='"today", "tomorrow", or YYYY-MM-DD')
    parser.add_argument("--strategy", "-s", type=int, choices=[1, 2, 3, 4], default=None,
                        help="Strategy preset (1=Butterfly Hold, 2=Butterfly 60%% TP, "
                             "3=Condor 60%% TP, 4=Condor Hold)")
    parser.add_argument("--quantity", type=int, default=1, help="Number of contracts (default: 1)")
    parser.add_argument("--ratio", type=float, default=2.0,
                        help="Target max_loss/max_profit ratio (default: 2.0)")
    parser.add_argument("--short-offset", type=float, default=0.0,
                        help="Short strikes N%% OTM (default: 0 = ATM butterfly)")
    parser.add_argument("--output", "-o", default=None, help="Output JSON file path")
    parser.add_argument("--submit", action="store_true", help="Submit the order")
    parser.add_argument("--bracket", nargs=2, type=float, metavar=("PROFIT", "STOP_LOSS"),
                        help="Bracket orders: profit target + stop-loss in dollars")
    parser.add_argument("--host", default="127.0.0.1", help="IB Gateway host")
    parser.add_argument("--port", type=int, default=4002, help="IB Gateway port")

    args = parser.parse_args()

    if args.strategy is not None:
        preset = STRATEGIES[args.strategy]
        args.short_offset = preset["short_offset"]
        args.ratio = preset["ratio"]

    expiry_date = parse_expiry(args.expiry)
    is_condor = args.short_offset > 0
    default_prefix = "iron_condor" if is_condor else "iron_butterfly"
    output_file = args.output or f"{default_prefix}_{expiry_date}.json"

    if args.strategy is not None:
        preset = STRATEGIES[args.strategy]
        strategy_type = f"Strategy {args.strategy}: {preset['name']}"
    else:
        strategy_type = "Iron Condor" if is_condor else "Iron Butterfly"
        if is_condor:
            strategy_type += f" (shorts {args.short_offset}% OTM)"

    print(f"Strategy:      {strategy_type}")
    print(f"Target expiry: {expiry_date} ({expiry_date.strftime('%A')})")
    print(f"Quantity:      {args.quantity}")
    print()

    print("[1/5] Connecting to IB Gateway ...")
    ib = connect(args.host, args.port)
    print("       Connected.")

    spx = ib.qualifyContracts(Index("SPX", "CBOE"))[0]
    spx_price = get_last(ib, spx)
    print(f"       SPX: {spx_price:.2f}")

    strategy = build_strategy(ib, spx_price, expiry_date, ratio=args.ratio,
                              short_offset=args.short_offset)
    display_strategy(strategy, args.quantity, strategy_num=args.strategy)

    bag = build_combo_contract(strategy)

    serializable_legs = [
        {k: v for k, v in leg.items() if k != "contract"}
        for leg in strategy["legs"]
    ]
    order_json = {
        "metadata": {
            "strategy": strategy.get("strategy_name", "iron_butterfly"),
            "symbol": "SPX",
            "expiry": strategy["expiry"],
            "net_credit": strategy["net_credit"],
            "max_profit": strategy["max_profit"],
            "max_loss": strategy["max_loss"],
            "ratio": strategy["ratio"],
            "legs": serializable_legs,
        }
    }
    with open(output_file, "w") as f:
        json.dump(order_json, f, indent=2)
    print(f"\nStrategy saved to: {output_file}")

    profit_target_pct = None
    if args.strategy is not None:
        profit_target_pct = STRATEGIES[args.strategy].get("profit_target_pct")

    if args.bracket and args.submit:
        submit_with_bracket(ib, bag, strategy, args.quantity,
                            bracket_profit=args.bracket[0], bracket_stop=args.bracket[1])
    elif profit_target_pct is not None and args.submit:
        submit_with_bracket(ib, bag, strategy, args.quantity,
                            profit_target_pct=profit_target_pct)
    elif args.submit:
        combo_bid, combo_ask = get_combo_price(ib, bag)
        if combo_ask is not None:
            entry_price = round_to_tick(combo_ask)
            print(f"\n  Combo bid={combo_bid}  ask={combo_ask}")
        else:
            entry_price = round_to_tick(-strategy["net_credit"])
            print(f"\n  Using leg-derived price: {entry_price}")

        order = LimitOrder("BUY", args.quantity, entry_price)
        trade = ib.placeOrder(bag, order)
        filled = wait_for_fill(ib, trade)
        if filled:
            print(f"  Filled @ {trade.orderStatus.avgFillPrice:.2f}")
        else:
            print(f"  Not filled after timeout. Order remains active.")
    else:
        print(f"\n  [DRY RUN] Add --submit to place the order.")

    ib.disconnect()


if __name__ == "__main__":
    main()
