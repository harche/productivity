# Connection & Session

## Connect

```python
from ib_async import IB
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1, timeout=20)
```

- **Gateway** ports: **4002** = paper, **4001** = live
- **TWS** ports: **7497** = paper, **7496** = live
- **Always use `clientId=1`** — reusing the same ID prevents stale sessions leaking in IB Gateway
- Always call `ib.disconnect()` when done

## Port Fallback

Try all known ports — paper first, then live, across both TWS and Gateway:

```python
from ib_async import IB
ib = IB()
connected = False
for port in [7497, 4002, 7496, 4001]:
    try:
        ib.connect('127.0.0.1', port, clientId=1, timeout=10)
        connected = True
        break
    except ConnectionRefusedError:
        continue
if not connected:
    raise RuntimeError('Could not connect — start TWS or IB Gateway and enable API')
```

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

**When market IS open but price is still NaN**, the gateway is likely not connected to the US data farm (`usfarm`). This happens when the gateway starts in a stale state. Fix: kill the gateway, restart it, and re-authenticate at `https://localhost:5000`. Verify farm status by listening for error events on connect — look for `code=2104, msg="Market data farm connection is OK:usfarm"`. If you only see `hfarm` or other non-US farms, the gateway needs a restart.

## Multi-Account Selection

With multiple accounts (e.g. TFSA, RRSP, Individual), use `managedAccounts()` to list them and `order.account` to target a specific one:

```python
accounts = ib.managedAccounts()  # returns list of account IDs
# Present accounts to user via AskUserQuestion and let them pick
```

- **`ib.managedAccounts()`** — returns `list[str]` of account IDs, available immediately after `connect()`
- **`order.account`** — set before `placeOrder()` to route to that account; defaults to `''` (primary account)
- **Never assume an account** — always present the list via `AskUserQuestion` and use the one the user selects
- **Do NOT use `reqManagedAccts()`** — it does not exist in `ib_async`; use `managedAccounts()` instead

## Keepalive

ib_async handles keepalive automatically — no tickle calls needed.
