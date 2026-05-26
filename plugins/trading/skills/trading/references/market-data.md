# Market Data & Pricing

## Requesting Prices

```python
ticker = ib.reqMktData(contract)
ib.sleep(3)
# Read prices
bid = ticker.bid
ask = ticker.ask
last = ticker.last
close = ticker.close  # previous close
# Clean up
ib.cancelMktData(contract)
```

**Wait at least 3 seconds** after `reqMktData` — data doesn't arrive instantly.

**Always cancel** when done to avoid subscription leaks.

## Invalid Prices

ib_async uses two sentinels for missing data:

| Value | Meaning | Check |
|-------|---------|-------|
| `nan` | Field not available | `util.isNan(val)` |
| `-1` | Empty price (market closed) | `val == -1` |

**Both must be treated as missing.** Use this helper:

```python
from ib_async import util

def valid_price(val):
    if util.isNan(val) or val == -1:
        return None
    return val
```

**Fallback:** When bid/ask are unavailable (market closed), use `ticker.close` (previous session close) as an estimate.

## Delayed Data Fallback

If you get error 10089 ("requires additional subscription"), fall back to delayed data. **Always tell the user the prices are delayed.**

```python
ib.reqMarketDataType(3)  # 3 = delayed
ticker = ib.reqMktData(contract)
ib.sleep(5)
# Prices arrive in ticker.last, ticker.bid, ticker.ask as usual
# IMPORTANT: inform the user these are delayed (typically 15 min)
```

Reset to live data with `ib.reqMarketDataType(1)` when done.

## Greeks

Greeks are on `ticker.modelGreeks` after requesting market data:

```python
ticker = ib.reqMktData(contract)
ib.sleep(3)
g = ticker.modelGreeks
if g:
    delta = g.delta      # negative for puts, positive for calls
    gamma = g.gamma
    theta = g.theta
    vega = g.vega
    iv = g.impliedVol
```

Greeks may be `None` if the pricing model hasn't run yet — always check before use.

## Multiple Contracts

Request in parallel for speed:

```python
tickers = [ib.reqMktData(c) for c in contracts]
ib.sleep(3)
for t in tickers:
    print(t.contract.localSymbol, valid_price(t.bid), valid_price(t.ask))
for t in tickers:
    ib.cancelMktData(t.contract)
```

## Price Rounding

Options prices must be rounded to the tick size:

```python
TICK_SIZE = 0.05  # SPX options on CBOE/SMART

def round_to_tick(price, tick=0.05):
    return round(round(price / tick) * tick, 2)
```

The double-round prevents floating-point drift.
