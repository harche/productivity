# Market Data & Pricing

## Requesting Prices (Two-Call Pattern)

Snapshots require two calls — first primes the subscription, second reads data:

```bash
# Prime
curl -sk "https://localhost:5000/v1/api/iserver/marketdata/snapshot?conids=265598&fields=31,84,86"
sleep 3
# Read
curl -sk "https://localhost:5000/v1/api/iserver/marketdata/snapshot?conids=265598&fields=31,84,86"
```

Multiple contracts: comma-separated conids.

```python
import requests, time, urllib3
urllib3.disable_warnings()

BASE = "https://localhost:5000/v1/api"
conids = "265598,272093"
fields = "31,84,86"
url = f"{BASE}/iserver/marketdata/snapshot?conids={conids}&fields={fields}"

requests.get(url, verify=False)  # prime
time.sleep(2.5)
data = requests.get(url, verify=False).json()  # read
```

**Use `/iserver/marketdata/snapshot`**, NOT `/md/snapshot`.

## Snapshot Field IDs

| Field | Description |
|-------|-------------|
| 31 | Last price |
| 55 | Symbol |
| 70 | High |
| 71 | Low |
| 82 | Change |
| 83 | Change % |
| 84 | Bid price |
| 85 | Bid size |
| 86 | Ask price |
| 87 | Volume |
| 7295 | Open |
| 7296 | Close |
| 7308 | Delta |
| 7309 | Gamma |
| 7310 | Theta |
| 7311 | Vega |
| 7633 | Implied Volatility |

## Price Parsing

Snapshot values are strings that may have prefixes:

| Prefix | Meaning |
|--------|---------|
| `C` | Derived from close (e.g. `"C39.36"`) |
| `H` | Halted |

Strip the prefix before converting to float:

```python
def parse_price(val):
    if val is None:
        return None
    s = str(val).lstrip("CHT")
    try:
        return float(s)
    except (ValueError, TypeError):
        return None
```

## Staleness Detection

Each snapshot includes an `_updated` timestamp (epoch milliseconds). Check if data is stale:

```python
import time

updated_ms = item.get("_updated", 0)
age_seconds = (time.time() * 1000 - updated_ms) / 1000
if age_seconds > 10:
    print(f"WARNING: snapshot is {age_seconds:.0f}s old")
```

## Greeks

Request Greeks via snapshot fields 7308-7311 and 7633:

```bash
curl -sk "https://localhost:5000/v1/api/iserver/marketdata/snapshot?conids=OPTION_CONID&fields=84,86,7308,7309,7310,7311,7633"
```

Parse with `parse_price()` — Greek values may also have string prefixes.

## Price Rounding

SPX option prices must be rounded to 0.05 tick size:

```python
TICK_SIZE = 0.05

def round_to_tick(price, tick=0.05):
    return round(round(price / tick) * tick, 2)
```

## Gotchas

- First snapshot call always returns minimal data — always do the two-call pattern.
- Combo snapshots need 6-8 seconds to populate, not 2.5.
- Field values are strings, not floats — always parse.
- During market close, some fields return `None` or are absent entirely.
