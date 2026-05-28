# Options: Contracts, Chains, Strikes

## Trading Classes

SPX has two trading classes:

| Class | Expiry | Symbol |
|-------|--------|--------|
| **SPXW** | Weeklies (Mon–Fri, daily 0DTE) | `SPXW  260527P07450000` |
| **SPX** | Monthlies (3rd Friday) | `SPX   260620P07450000` |

## Finding the Right Trading Class for an Expiry

```python
from ib_async import Index
spx = ib.qualifyContracts(Index('SPX', 'CBOE'))[0]
chains = ib.reqSecDefOptParams(spx.symbol, '', spx.secType, spx.conId)

expiry = '20260527'
trading_class = 'SPXW'  # default
for chain in chains:
    if chain.exchange == 'SMART' and expiry in chain.expirations:
        trading_class = chain.tradingClass
        break
```

Always check `reqSecDefOptParams` — if the expiry isn't in any chain, the contract doesn't exist.

## Available Expirations

```python
chains = ib.reqSecDefOptParams(spx.symbol, '', spx.secType, spx.conId)
for chain in chains:
    if chain.exchange == 'SMART':
        print(f'{chain.tradingClass}: {sorted(chain.expirations)[:10]}...')
```

Use this to verify an expiry exists before building a strategy.

## Qualifying a Contract

```python
from ib_async import Option
opt = Option(
    symbol='SPX',
    lastTradeDateOrContractMonth=expiry,  # '20260527'
    strike=7450,
    right='P',          # 'P' or 'C'
    exchange='SMART',
    currency='USD',
    tradingClass='SPXW'
)
qualified = ib.qualifyContracts(opt)
if qualified[0] is None:
    raise RuntimeError(f'Contract does not exist: {opt}')
contract = qualified[0]
# contract.conId is now populated
```

**Always qualify before use** — it fills in `conId` and validates the contract exists.

## Available Strikes

```python
chains = ib.reqSecDefOptParams(spx.symbol, '', spx.secType, spx.conId)
for chain in chains:
    if chain.exchange == 'SMART' and chain.tradingClass == 'SPXW':
        strikes = sorted(chain.strikes)
        print(f'Strikes: {strikes[:5]}...{strikes[-5:]}')
        break
```

Use this to verify a strike exists before trying to qualify it.

## Strike Rounding

SPX strikes come in 5-point increments:

```python
STRIKE_INCREMENT = 5

def round_to_strike(value):
    return round(value / STRIKE_INCREMENT) * STRIKE_INCREMENT
```

Example: SPX at 7473.5 → nearest strikes are 7470 and 7475.

## Finding Strikes by Delta

Professional strike selection uses delta, not fixed percentages. Common targets:

| Target | Delta (put) | Delta (call) | Approx. probability OTM |
|--------|-------------|--------------|------------------------|
| 1 SD   | -0.16       | +0.16        | ~84%                   |
| Conservative | -0.10  | +0.10        | ~90%                   |
| Aggressive   | -0.25  | +0.25        | ~75%                   |

### Scan a range of strikes for target delta

```python
STRIKE_INC = 5

def find_strike_by_delta(ib, expiry, tc, target_delta, right, spx_price, avail_strikes):
    """Find the strike closest to target_delta.
    
    Args:
        target_delta: negative for puts (e.g. -0.16), positive for calls (e.g. 0.16)
        right: 'P' or 'C'
    Returns:
        (strike, actual_delta) or (None, None) if Greeks unavailable
    """
    # Scan 200 points around ATM in 5-point increments
    scan_low = round_to_strike(spx_price - 200)
    scan_high = round_to_strike(spx_price + 200)
    scan_strikes = [s for s in range(scan_low, scan_high + 1, STRIKE_INC)
                    if s in avail_strikes]

    contracts = [Option('SPX', expiry, s, right, 'SMART', tradingClass=tc)
                 for s in scan_strikes]
    qualified = [c for c in ib.qualifyContracts(*contracts) if c is not None]
    if not qualified:
        return None, None

    tickers = [ib.reqMktData(c) for c in qualified]
    ib.sleep(5)

    best_strike, best_delta, best_diff = None, None, float('inf')
    for t in tickers:
        g = t.modelGreeks
        if g and g.delta is not None:
            diff = abs(g.delta - target_delta)
            if diff < best_diff:
                best_diff = diff
                best_strike = t.contract.strike
                best_delta = g.delta

    for t in tickers:
        ib.cancelMktData(t.contract)

    return best_strike, best_delta
```

### Find both sides for an iron condor

```python
# 16-delta iron condor: ~1 standard deviation on each side
put_strike, put_delta = find_strike_by_delta(
    ib, expiry, tc, -0.16, 'P', spx_price, avail_strikes)
call_strike, call_delta = find_strike_by_delta(
    ib, expiry, tc, 0.16, 'C', spx_price, avail_strikes)

if put_strike and call_strike:
    print(f'Short put:  {put_strike} (delta {put_delta:.3f})')
    print(f'Short call: {call_strike} (delta {call_delta:.3f})')
else:
    print('Greeks unavailable — fall back to percentage-based strikes')
    # See strategies.md Step 2 for percentage fallback
```

### Fallback when Greeks are unavailable

Greeks require live market data. During off-hours or without data subscriptions, `modelGreeks` returns None. Fall back to the percentage-based approach and warn the user:

```python
if put_strike is None:
    offset_pct = 0.003  # 0.3% ≈ rough 16-delta proxy for short-dated SPX
    put_strike = round_to_strike(spx_price * (1 - offset_pct))
    call_strike = round_to_strike(spx_price * (1 + offset_pct))
    print(f'WARNING: Using {offset_pct*100:.1f}% offset (Greeks unavailable)')
```
