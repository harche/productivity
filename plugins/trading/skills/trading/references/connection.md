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
[ticker] = ib.reqTickers(spx)
ib.sleep(2)
price = ticker.marketPrice()  # or ticker.last / ticker.close
```

## Keepalive

ib_async handles keepalive automatically — no tickle calls needed.
