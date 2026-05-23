# Connection & Session

## Connect

```python
from ib_async import IB
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1, timeout=20)
```

- Port **4002** = paper trading, **4001** = live
- **Always use `clientId=1`** — reusing the same ID prevents stale sessions leaking in IB Gateway
- Always call `ib.disconnect()` when done

## Async Waits

Use `ib.sleep(N)`, never `time.sleep(N)`. ib_async is event-driven — `time.sleep` blocks the event loop and prevents data from arriving.

## SPX Price

```python
from ib_async import Index
spx = ib.qualifyContracts(Index('SPX', 'CBOE'))[0]
ticker = ib.reqMktData(spx)
ib.sleep(3)
price = ticker.marketPrice()
ib.cancelMktData(spx)
```

**When market is closed**, `marketPrice()` returns NaN. Fallback chain:

```python
from ib_async import util
for val in [ticker.last, ticker.close]:
    if not util.isNan(val) and val != -1:
        price = val
        break
```

## Keepalive

ib_async handles keepalive automatically — no tickle calls needed.
