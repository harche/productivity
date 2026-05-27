# Economic Calendar & Pre-Trade Checks

## IBKR Wall Street Horizon (WSH) Events

IBKR provides economic and corporate event data through Wall Street Horizon. Query upcoming events before entering trades.

```python
from ib_async import IB
from ib_async.objects import WshEventData
import json

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1, timeout=20)

# Get events for the next 7 days
data = WshEventData(
    startDate='20260526',
    endDate='20260602',
    totalLimit=50,
)
result = ib.getWshEventData(data)
if result:
    print(result)
```

### Filter by portfolio holdings

```python
# Only events affecting your current positions
data = WshEventData(fillPortfolio=True, totalLimit=20)
result = ib.getWshEventData(data)
```

### Filter by specific contract

```python
# Events for SPX specifically
from ib_async import Index
spx = ib.qualifyContracts(Index('SPX', 'CBOE'))[0]
data = WshEventData(conId=spx.conId, totalLimit=10)
result = ib.getWshEventData(data)
```

## Cross-Skill: FRED Economic Data

Use the `financial-research:economic-data` skill to check macro conditions before trading. Key series to check:

| Check | FRED Series | What to look for |
|-------|-------------|-----------------|
| VIX level | `VIXCLS` | < 14 = thin premiums, > 30 = fat but dangerous |
| Fed rate | `DFEDTARU` | Rate changes = regime shifts |
| CPI trend | `CPIAUCSL` (units=pc1) | Surprises move SPX 1-3% |

**How to use**: Before suggesting a 0DTE or short-dated trade, invoke the `financial-research:economic-data` skill to pull current VIX and check recent CPI/NFP release dates. This is a separate skill invocation, not ib_async code.

## Known High-Impact Economic Events

These events are scheduled well in advance. The exact dates change each month/quarter, but the pattern is consistent:

| Event | Frequency | Typical Time (ET) | Typical SPX Impact |
|-------|-----------|-------------------|-------------------|
| FOMC Decision | 8x/year | 2:00 PM | 1-3% intraday |
| CPI Report | Monthly | 8:30 AM | 1-2% intraday |
| Nonfarm Payrolls (NFP) | Monthly (1st Friday) | 8:30 AM | 0.5-1.5% intraday |
| GDP (advance) | Quarterly | 8:30 AM | 0.5-1% |
| PCE Price Index | Monthly | 8:30 AM | 0.5-1% |
| FOMC Minutes | 3 weeks after decision | 2:00 PM | 0.5-1% |
| Jackson Hole / Fed speeches | Irregular | Varies | 0.5-2% |

## Pre-Trade Decision Table

Check these conditions before entering any SPX options strategy:

### Event Risk

| Condition | DTE | Action |
|-----------|-----|--------|
| FOMC/CPI/NFP within 2 hours | 0 | **Do not enter** |
| FOMC/CPI/NFP within 2 hours | 1-7 | Widen wings or reduce size by 50% |
| FOMC/CPI/NFP within 2 hours | > 7 | Proceed with normal sizing |
| FOMC/CPI/NFP today but already passed | any | OK if IV has normalized (check VIX) |

### Volatility Regime

| VIX Level | Regime | Premium Quality | Recommendation |
|-----------|--------|----------------|----------------|
| < 14 | Ultra-low vol | Thin | Skip or reduce size — risk/reward poor |
| 14-20 | Normal | Fair | Standard sizing |
| 20-30 | Elevated | Fat | Good environment for premium selling |
| > 30 | Crisis | Very fat | Reduce size — moves are violent and correlated |

### Time of Day (0DTE specific)

| Window | Risk | Recommendation |
|--------|------|----------------|
| Pre-market (before 9:30 ET) | No liquidity | Do not enter |
| 9:30-10:00 ET | Opening volatility | Wait for direction to establish |
| 10:00-14:00 ET | Best window | Enter here |
| 14:00-15:00 ET | Gamma acceleration | Only if > 50% profit target already |
| 15:00-16:00 ET | Extreme gamma | Close all positions, do not enter new |

## Gotchas

- WSH data requires a Wall Street Horizon subscription on some IBKR account types. Paper trading accounts may return empty results — test first.
- VIX from FRED (`VIXCLS`) is end-of-day. For intraday VIX, use ib_async: `ib.qualifyContracts(Index('VIX', 'CBOE'))` then `reqMktData`.
- Economic events can leak early (via "sources say" reporting) — IV often rises hours before the official release.
- FOMC days have a specific pattern: low vol before 2 PM, then a spike. Don't mistake pre-announcement calm for safety.
