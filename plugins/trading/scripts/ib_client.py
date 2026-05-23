#!/usr/bin/env python3
"""
Shared helpers for IBKR trading scripts.

Reuses from upstream:
  - ibkrbox: get_last(), get_limit() (pure functions that work with ib_async)
  - ib_async: IB, Option, ComboLeg, Contract, LimitOrder, Index, etc.

Note: ibkrbox's get_ib(), get_expiry(), get_strikes(), box_trade() use ib_insync
internally which is broken with IB Gateway 10.45+. We use ib_async.IB directly
for the connection and inline the ~5 line functions that need it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ib_async import (
    IB,
    ComboLeg,
    Contract,
    FuturesOption,
    Index,
    LimitOrder,
    Option,
    Ticker,
    Trade,
    util,
)
from ibkrbox.ibkrbox import get_last, get_limit  # these work with ib_async.IB

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4002
TICK_SIZE = 0.05


def connect(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, client_id: int = 1) -> IB:
    """Connect to IB Gateway. Returns an ib_async.IB instance.

    All scripts should use the same clientId (default 1) to avoid
    leaking stale client sessions in the gateway.
    """
    ib = IB()
    ib.connect(host, port, clientId=client_id, timeout=20)
    return ib


def round_to_tick(price: float, tick: float = TICK_SIZE) -> float:
    return round(round(price / tick) * tick, 2)


# --- Ported from ibkrbox (5 lines each, use ib_async instead of ib_insync) ---

def get_spx_price(ib: IB) -> float:
    """Get SPX last price. Uses ibkrbox's get_last with ib_async contract."""
    spx = ib.qualifyContracts(Index("SPX", "CBOE"))[0]
    return get_last(ib, spx)


def get_expiry(ib: IB, months: int) -> str:
    """Find SPX option expiry closest to N months out. Ported from ibkrbox."""
    spx = ib.qualifyContracts(Index("SPX", "CBOE"))[0]
    chain = next(
        c for c in ib.reqSecDefOptParams(spx.symbol, "", spx.secType, spx.conId)
        if c.tradingClass == "SPX" and c.exchange == "SMART"
    )
    expdays = [
        abs(months * 30 - (datetime.strptime(exp, "%Y%m%d") - datetime.now()).days)
        for exp in chain.expirations
    ]
    _, idx = min((v, i) for i, v in enumerate(expdays))
    return chain.expirations[idx]


def get_strikes(ib: IB, amount: float) -> tuple[float, float]:
    """Auto-calculate box spread strikes centered on SPX. Ported from ibkrbox."""
    price = get_spx_price(ib)
    spread = int(amount / 100)
    strike = int(price / 100) * 100
    if spread <= 200:
        return strike, strike + spread
    rem = spread % 200
    remhalf = (spread - rem) / 2
    return strike - remhalf, strike + remhalf + rem


def box_trade(ib: IB, expiry: str, strike1: float, strike2: float, limit: float,
              quantity: int = 1, short: bool = False, acc: str = "",
              timeout: int = 20, max_price: float = None, execute: bool = False):
    """Build and optionally execute a box spread. Ported from ibkrbox."""
    assert strike1 < strike2
    if max_price is None:
        max_price = limit

    boxorder = ["SELL", "BUY", "BUY", "SELL"] if short else ["BUY", "SELL", "SELL", "BUY"]
    boxspread = [
        Option("SPX", expiry, S, T, exchange="SMART", tradingClass="SPX")
        for S in (strike1, strike2)
        for T in ("C", "P")
    ]
    boxspread = ib.qualifyContracts(*boxspread)

    legs = [
        ComboLeg(conId=c.conId, ratio=1, action=a, exchange="SMART")
        for c, a in zip(boxspread, boxorder)
    ]
    bag = Contract(symbol="SPX", secType="BAG", exchange="SMART", currency="USD", comboLegs=legs)

    df = util.df(boxspread)[["symbol", "strike", "right", "lastTradeDateOrContractMonth"]]
    df.loc[:, "action"] = [a for a in boxorder]
    print(f"\nBox Legs:\n{df}")

    mul = 100
    if not short:
        print(f"Lend {quantity * int(limit * mul)} today, receive {quantity * (strike2 - strike1) * mul} on {expiry}")
    else:
        print(f"Borrow {abs(quantity * int(limit * mul))} today, repay {quantity * (strike2 - strike1) * mul} on {expiry}")

    if not execute:
        return None

    return sweep_fill(ib, bag, "BUY", quantity, limit, max_price, timeout=timeout, account=acc)


# --- Helpers that don't exist upstream ---

def find_option_by_delta(tickers: list[Ticker], target_delta: float, side: str) -> Optional[Ticker]:
    """Find option with delta closest to target. Adapted from 0dte-trader."""
    target = abs(target_delta)
    best = None
    best_diff = float("inf")
    for t in tickers:
        if t.contract.right != side:
            continue
        greeks = t.modelGreeks
        if greeks is None or greeks.delta is None:
            continue
        diff = abs(abs(greeks.delta) - target)
        if diff < best_diff:
            best_diff = diff
            best = t
    return best


def build_combo(symbol: str, legs: list[tuple[Contract, str]], exchange: str = "SMART") -> Contract:
    """Build a BAG (combo) contract from (contract, action) pairs."""
    combo_legs = [
        ComboLeg(conId=contract.conId, ratio=1, action=action, exchange=exchange)
        for contract, action in legs
    ]
    return Contract(symbol=symbol, secType="BAG", exchange=exchange, currency="USD", comboLegs=combo_legs)


def sweep_fill(ib: IB, contract: Contract, action: str, quantity: int,
               start_price: float, max_price: float,
               step: float = TICK_SIZE, timeout: int = 20,
               account: str = "") -> Optional[Trade]:
    """Price sweep retry for fills. Adapted from ibkrbox box_trade()."""
    import numpy as np
    remaining = quantity
    last_trade = None
    mintick = step

    for price in np.arange(start_price, max_price + mintick, mintick):
        if remaining <= 0:
            break
        price = round_to_tick(float(price))
        print(f"  Placing: {action} {remaining}x @ {price:.2f} (waiting {timeout}s)...")
        trade = ib.placeOrder(contract, LimitOrder(action, remaining, price, account=account))
        try:
            ib.sleep(timeout)
        except KeyboardInterrupt:
            ib.cancelOrder(trade.order)
            return None

        if trade.filled() > 0:
            print(f"  Filled {trade.filled()} @ {trade.orderStatus.avgFillPrice:.2f}")
        if trade.filled() >= remaining:
            return trade

        ib.cancelOrder(trade.order)
        ib.sleep(3)
        remaining -= trade.filled()
        last_trade = trade

    return last_trade
