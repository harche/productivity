# Historical Data & Price Analysis

## Historical Price Bars

```bash
curl -sk -X POST "https://localhost:5000/v1/api/hmds/history" \
  -H "Content-Type: application/json" \
  -d '{"conid": 265598, "period": "1m", "bar": "1d"}'
```

```python
import requests, urllib3
urllib3.disable_warnings()

BASE = "https://localhost:5000/v1/api"

data = requests.post(f"{BASE}/hmds/history",
    json={"conid": 265598, "period": "1m", "bar": "1d"},
    verify=False).json()

for bar in data.get("data", []):
    print(f"O={bar['o']} H={bar['h']} L={bar['l']} C={bar['c']} V={bar['v']}")
```

Bar fields are abbreviated: `o` (open), `h` (high), `l` (low), `c` (close), `v` (volume), `t` (timestamp).

## Period Values

| Period | Description |
|--------|-------------|
| `1min` - `30min` | Minutes |
| `1h` - `8h` | Hours |
| `1d` - `5d` | Days |
| `1w` - `4w` | Weeks |
| `1m` - `12m` | Months |
| `1y` - `5y` | Years |

## Bar Sizes

| Bar | Description |
|-----|-------------|
| `1min` | 1 minute |
| `5min` | 5 minutes |
| `15min` | 15 minutes |
| `30min` | 30 minutes |
| `1h` | 1 hour |
| `1d` | 1 day |
| `1w` | 1 week |
| `1m` | 1 month |

## Outside Regular Trading Hours

```python
data = requests.post(f"{BASE}/hmds/history",
    json={"conid": 265598, "period": "1d", "bar": "1h", "outsideRth": True},
    verify=False).json()
```

## SPX Index Historical Data

```python
SPX_CONID = 416904
data = requests.post(f"{BASE}/hmds/history",
    json={"conid": SPX_CONID, "period": "1m", "bar": "1d"},
    verify=False).json()
```

## Gotchas

- Period and bar formats differ from ib_async: `"1m"` not `"1 M"`, `"1d"` not `"1 day"`.
- Rate-limited — avoid hammering in a loop. Add `time.sleep(1)` between requests.
- Intraday bars (1min to 1h) are only available for ~1 year back. Daily bars go back decades.
- `outsideRth: True` includes pre/post-market data.
- No `whatToShow` equivalent — always returns trade data.
