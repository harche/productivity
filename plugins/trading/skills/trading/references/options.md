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
if not qualified or qualified[0].conId == 0:
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
    return int(round(value / STRIKE_INCREMENT) * STRIKE_INCREMENT)
```

Example: SPX at 7473.5 → nearest strikes are 7470 and 7475.

## Finding Strikes by Delta

```python
# Get all options for an expiry
contracts = [Option('SPX', expiry, s, 'P', 'SMART', tradingClass='SPXW')
             for s in range(7400, 7550, 5)]
qualified = ib.qualifyContracts(*contracts)
tickers = [ib.reqMktData(c) for c in qualified if c.conId > 0]
ib.sleep(5)

# Find put closest to -0.16 delta
for t in tickers:
    g = t.modelGreeks
    if g and g.delta:
        print(f'{t.contract.strike}P delta={g.delta:.3f}')
```
