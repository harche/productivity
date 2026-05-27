# Historical Data & Price Analysis

## Historical Price Bars

```python
from ib_async import Stock, Index

contract = ib.qualifyContracts(Stock('AAPL', 'SMART', 'USD'))[0]

bars = ib.reqHistoricalData(
    contract,
    endDateTime='',       # empty string = now
    durationStr='1 M',    # how far back
    barSizeSetting='1 day',
    whatToShow='TRADES',
    useRTH=True,          # regular trading hours only
)
for b in bars:
    print(f'{b.date}: O={b.open} H={b.high} L={b.low} C={b.close} V={b.volume}')
```

Each bar has: `date`, `open`, `high`, `low`, `close`, `volume`, `barCount`, `average`.

## Duration Strings

| Duration | Format | Example |
|----------|--------|---------|
| Seconds | `S` | `'1800 S'` (30 min) |
| Days | `D` | `'5 D'` |
| Weeks | `W` | `'1 W'` |
| Months | `M` | `'6 M'` |
| Years | `Y` | `'1 Y'` |

## Bar Sizes

| Bar Size | Max Duration |
|----------|-------------|
| `'1 secs'` | 1800 S |
| `'5 secs'` | 3600 S |
| `'1 min'` | 1 D |
| `'5 mins'` | 1 W |
| `'15 mins'` | 2 W |
| `'30 mins'` | 1 M |
| `'1 hour'` | 1 M |
| `'1 day'` | 1 Y |
| `'1 week'` | multiple Y |
| `'1 month'` | multiple Y |

## whatToShow Options

| Value | Description | Works on |
|-------|-------------|----------|
| `'TRADES'` | Trade prices | Stocks, futures |
| `'MIDPOINT'` | Mid of bid/ask | Forex, some stocks |
| `'BID'` | Bid prices | Requires L1 subscription |
| `'ASK'` | Ask prices | Requires L1 subscription |
| `'OPTION_IMPLIED_VOLATILITY'` | IV over time | Stocks, indices |
| `'HISTORICAL_VOLATILITY'` | HV over time | Stocks, indices |

**BID/ASK/MIDPOINT may return empty bars** without the appropriate market data subscription.

## Earliest Available Data

```python
head = ib.reqHeadTimeStamp(contract, 'TRADES', useRTH=True)
print(f'Data available from: {head}')  # e.g., 1980-12-12 for AAPL
```

## Historical Ticks (Tick-Level Data)

```python
ticks = ib.reqHistoricalTicks(
    contract,
    startDateTime='20260527 09:30:00 US/Eastern',
    endDateTime='',         # leave empty when using startDateTime
    numberOfTicks=100,
    whatToShow='TRADES',
    useRth=True,
)
for t in ticks:
    print(f'{t.time}: price={t.price}, size={t.size}')
```

**You must specify exactly 2 of 3**: `startDateTime`, `endDateTime`, `numberOfTicks`. Leave the third as `''` or `0`.

## Histogram (Price Distribution)

```python
hist = ib.reqHistogramData(contract, useRTH=True, period='1 week')
for h in hist:
    print(f'price={h.price}, count={h.count}')
```

Shows where the stock has spent the most time — useful for identifying support/resistance levels.

Period values: `'1 day'`, `'1 week'`, `'1 month'`, `'3 months'`, `'6 months'`, `'1 year'`.

## SPX Index Historical Data

```python
spx = ib.qualifyContracts(Index('SPX', 'CBOE'))[0]
bars = ib.reqHistoricalData(spx, '', '1 M', '1 day', 'TRADES', True)
```

## Gotchas

- `endDateTime=''` means "now". To query a specific date range, pass a datetime or string like `'20260101 23:59:59 US/Eastern'`.
- IB rate-limits historical data requests — avoid hammering in a loop. Add `ib.sleep(1)` between requests if querying multiple symbols.
- Intraday bars (`1 min` to `1 hour`) are only available for ~1 year back. Daily bars go back decades.
- `useRTH=True` excludes pre/post-market data. Set `False` to include extended hours.
