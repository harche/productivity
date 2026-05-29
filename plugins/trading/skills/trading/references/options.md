# Options: Contracts, Chains, Strikes

## Trading Classes

SPX has two trading classes:

| Class | Expiry | Symbol |
|-------|--------|--------|
| **SPXW** | Weeklies (Mon–Fri, daily 0DTE) | `SPXW  260527P07450000` |
| **SPX** | Monthlies (3rd Friday) | `SPX   260620P07450000` |

The `tradingClass` field in the response tells you which one you got.

## Finding Available Expirations

```bash
curl -sk -X POST "https://localhost:5000/v1/api/iserver/secdef/search" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SPX", "secType": "OPT"}'
```

Response includes a `sections` array. The OPT section has a `months` field with available expirations like `"MAY26;JUN26;JUL26;AUG26;..."`.

## Available Strikes

```bash
curl -sk "https://localhost:5000/v1/api/iserver/secdef/strikes?conid=416904&sectype=OPT&month=JUN26&exchange=SMART"
```

Returns `{"call": [7000, 7005, ...], "put": [7000, 7005, ...]}`.

## Getting a Specific Option Contract

```bash
curl -sk "https://localhost:5000/v1/api/iserver/secdef/info?conid=416904&sectype=OPT&month=JUN26&exchange=SMART&strike=7450&right=P"
```

Returns an array of contracts matching the criteria. Each has `conid`, `desc2` (human-readable like `"JUN 27 '26 7450 Put"`), `maturityDate`, `tradingClass`, `multiplier`.

Multiple results = multiple expiry dates within that month. Pick by `maturityDate`.

## Strike Rounding

SPX strikes come in 5-point increments:

```python
STRIKE_INCREMENT = 5

def round_to_strike(value):
    return round(value / STRIKE_INCREMENT) * STRIKE_INCREMENT
```

## Finding Strikes by Delta

Scan candidate strikes and pick the one closest to target delta:

```python
import requests, time, urllib3
urllib3.disable_warnings()

BASE = "https://localhost:5000/v1/api"

def find_strike_by_delta(underlying_conid, month, right, target_delta, spx_price):
    """Find strike closest to target_delta.
    target_delta: negative for puts (e.g. -0.16), positive for calls (e.g. 0.16)
    """
    # Get available strikes
    strikes_data = requests.get(
        f"{BASE}/iserver/secdef/strikes",
        params={"conid": underlying_conid, "sectype": "OPT", "month": month, "exchange": "SMART"},
        verify=False
    ).json()
    
    strike_list = strikes_data["put"] if right == "P" else strikes_data["call"]
    
    # Narrow to ~200 points around ATM
    candidates = [s for s in strike_list if abs(s - spx_price) <= 200]
    
    # Get conids for candidate strikes
    contracts = []
    for strike in candidates:
        resp = requests.get(
            f"{BASE}/iserver/secdef/info",
            params={"conid": underlying_conid, "sectype": "OPT", "month": month,
                    "exchange": "SMART", "strike": strike, "right": right},
            verify=False
        ).json()
        if isinstance(resp, list) and resp:
            contracts.append({"conid": resp[0]["conid"], "strike": strike})
    
    # Get deltas via snapshot
    conids = ",".join(str(c["conid"]) for c in contracts)
    requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={conids}&fields=7308", verify=False)
    time.sleep(3)
    data = requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={conids}&fields=7308", verify=False).json()
    
    best_strike, best_delta, best_diff = None, None, float("inf")
    for item in data:
        delta_val = item.get("7308")
        if delta_val is None:
            continue
        delta = float(str(delta_val).lstrip("CHT"))
        diff = abs(delta - target_delta)
        conid = item["conid"]
        strike = next(c["strike"] for c in contracts if c["conid"] == conid)
        if diff < best_diff:
            best_diff = diff
            best_strike = strike
            best_delta = delta
    
    return best_strike, best_delta
```

### Common delta targets

| Target | Delta (put) | Delta (call) | Approx. probability OTM |
|--------|-------------|--------------|------------------------|
| 1 SD | -0.16 | +0.16 | ~84% |
| Conservative | -0.10 | +0.10 | ~90% |
| Aggressive | -0.25 | +0.25 | ~75% |

### Fallback when Greeks are unavailable

```python
if best_strike is None:
    offset_pct = 0.003  # 0.3% ≈ rough 16-delta proxy for short-dated SPX
    put_strike = round_to_strike(spx_price * (1 - offset_pct))
    call_strike = round_to_strike(spx_price * (1 + offset_pct))
    print(f"WARNING: Using {offset_pct*100:.1f}% offset (Greeks unavailable)")
```

## Gotchas

- `/iserver/secdef/info` can return transient 500 errors — retry up to 2 times.
- Month format is `MAY26`, `JUN26`, `JAN27` — NOT `20260527`.
- Multiple results from `/iserver/secdef/info` mean multiple expiry dates — filter by `maturityDate`.
- The `strike` parameter must exactly match an available strike — use `/iserver/secdef/strikes` first.
