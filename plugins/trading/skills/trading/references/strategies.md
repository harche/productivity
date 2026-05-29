# Strategies: Iron Butterfly & Iron Condor

## Strategy Presets

Default recommendation: **Strategy 3** — best risk-adjusted returns.

| # | Name | Short Strikes | Exit |
|---|------|--------------|------|
| 1 | Iron Butterfly — Hold to Expiry | ATM | Hold |
| 2 | Iron Butterfly — 60% Profit Target | ATM | Buy back at 40% of credit |
| 3 | Iron Condor — 60% Profit Target | 0.3% OTM each side | Buy back at 40% of credit |
| 4 | Iron Condor — Hold to Expiry | 0.3% OTM each side | Hold |
| 5 | **Iron Condor — 16-Delta, 60% PT** | 16-delta each side | Buy back at 40% of credit |
| 6 | Iron Condor — 16-Delta, Hold | 16-delta each side | Hold |

Strategies 5-6 use delta-based strike selection (see [options.md](options.md) `find_strike_by_delta`). Preferred over percentage-based when Greeks are available — delta adapts to current volatility.

For pre-trade event checks, use the `financial-research:economic-data` skill to check VIX, FOMC dates, CPI releases, etc.

## Constructing an Iron Butterfly / Condor

### Step 1: Get SPX price

```python
import requests, time, urllib3
urllib3.disable_warnings()

BASE = "https://localhost:5000/v1/api"
SPX_CONID = 416904

# Initialize session
requests.get(f"{BASE}/iserver/accounts", verify=False)

# Get SPX price
requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={SPX_CONID}&fields=31", verify=False)
time.sleep(3)
data = requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={SPX_CONID}&fields=31", verify=False).json()
spx_price = float(str(data[0].get("31", "0")).lstrip("CHT"))
```

### Step 2: Pick short strikes

**Iron Butterfly (ATM):** both shorts at nearest strike to SPX.

```python
STRIKE_INC = 5
atm = int(round(spx_price / STRIKE_INC) * STRIKE_INC)
short_put_strike = atm
short_call_strike = atm
```

**Iron Condor — Delta-Based (Strategies 5-6):** see [options.md](options.md) for `find_strike_by_delta`.

**Iron Condor — Percentage-Based (Strategies 3-4):**

```python
offset_pct = 0.003  # 0.3%
short_put_strike = int(round((spx_price * (1 - offset_pct)) / STRIKE_INC) * STRIKE_INC)
short_call_strike = int(round((spx_price * (1 + offset_pct)) / STRIKE_INC) * STRIKE_INC)
```

### Step 3: Find option contracts for short legs

```python
month = "MAY26"  # adjust to target month

# Get contract conids for short legs
def get_contract(strike, right, month, maturity=None):
    resp = requests.get(f"{BASE}/iserver/secdef/info",
        params={"conid": SPX_CONID, "sectype": "OPT", "month": month,
                "exchange": "SMART", "strike": strike, "right": right},
        verify=False).json()
    if not isinstance(resp, list) or not resp:
        raise RuntimeError(f"Contract not found: {strike}{right} {month}")
    if maturity:
        match = [c for c in resp if c["maturityDate"] == maturity]
        return match[0] if match else resp[0]
    return resp[0]

sp = get_contract(short_put_strike, "P", month)
sc = get_contract(short_call_strike, "C", month)
```

### Step 4: Price the shorts

```python
conids = f"{sp['conid']},{sc['conid']}"
requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={conids}&fields=84,86", verify=False)
time.sleep(3)
data = requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={conids}&fields=84,86", verify=False).json()

def parse_price(val):
    if val is None: return None
    try: return float(str(val).lstrip("CHT"))
    except: return None

prices = {}
for item in data:
    prices[item["conid"]] = {
        "bid": parse_price(item.get("84")),
        "ask": parse_price(item.get("86"))
    }

sp_mid = (prices[sp["conid"]]["bid"] + prices[sp["conid"]]["ask"]) / 2
sc_mid = (prices[sc["conid"]]["bid"] + prices[sc["conid"]]["ask"]) / 2
net_credit_shorts = sp_mid + sc_mid
```

### Step 5: Calculate wing strikes

Wing width determines max loss. Target: `(ratio + 1) × net_credit`.

```python
ratio = 2.0  # max_loss = 2× max_profit
wing_width = int(round((ratio + 1.0) * net_credit_shorts / STRIKE_INC) * STRIKE_INC)
wing_width = max(wing_width, STRIKE_INC)

long_put_strike = short_put_strike - wing_width
long_call_strike = short_call_strike + wing_width
```

Verify strikes exist using `/iserver/secdef/strikes`.

### Ratio Selection Guide

| Ratio | Max Loss:Profit | Credit | Best for |
|-------|----------------|--------|----------|
| 1.5 | 1.5:1 | Lower | Passive — no rolling or adjustments |
| **2.0** | **2:1** | **Moderate** | **Active management (60% PT + exit rules)** |
| 2.5 | 2.5:1 | Higher | Aggressive — strict stop-losses required |

### Step 6: Get wing contracts and price them

```python
lp = get_contract(long_put_strike, "P", month)
lc = get_contract(long_call_strike, "C", month)

wing_conids = f"{lp['conid']},{lc['conid']}"
requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={wing_conids}&fields=84,86", verify=False)
time.sleep(3)
wing_data = requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={wing_conids}&fields=84,86", verify=False).json()

for item in wing_data:
    prices[item["conid"]] = {
        "bid": parse_price(item.get("84")),
        "ask": parse_price(item.get("86"))
    }

lp_mid = (prices[lp["conid"]]["bid"] + prices[lp["conid"]]["ask"]) / 2
lc_mid = (prices[lc["conid"]]["bid"] + prices[lc["conid"]]["ask"]) / 2
```

### Step 7: Calculate strategy metrics

```python
net_credit = net_credit_shorts - lp_mid - lc_mid
actual_wing = max(short_put_strike - long_put_strike, long_call_strike - short_call_strike)
max_profit = net_credit * 100
max_loss = (actual_wing - net_credit) * 100

print(f"Net Credit:  ${net_credit:.2f} (${max_profit:,.0f})")
print(f"Max Loss:    ${max_loss:,.0f}")
print(f"Wing Width:  {actual_wing} points")
print(f"Breakevens:  {short_put_strike - net_credit:.2f} / {short_call_strike + net_credit:.2f}")
```

### Step 8: Build conidex and submit

```python
conidex = f"{SPX_CONID};;;{lp['conid']}/1,{sp['conid']}/-1,{sc['conid']}/-1,{lc['conid']}/1"

body = {"orders": [{
    "conidex": conidex,
    "orderType": "LMT",
    "side": "BUY",
    "price": round(net_credit * -1, 2),  # negative = credit
    "quantity": 1,
    "tif": "GTC"
}]}
```

See [orders.md](orders.md) for confirmation chain handling.

### 60% Profit Target Exit

After entry fills, place a standing LMT order to buy back at 40% of credit:

```python
close_conidex = reverse_conidex(conidex)  # see positions.md
close_price = round(net_credit * 0.40, 2)

close_body = {"orders": [{
    "conidex": close_conidex,
    "orderType": "LMT",
    "side": "BUY",
    "price": round(close_price, 2),
    "quantity": 1,
    "tif": "GTC"
}]}
```

## Gotchas

- Wing strikes may not exist for all expirations — always validate with `/iserver/secdef/strikes`.
- Iterating wing width: wing prices reduce net credit, which changes required wing width. May need 2-3 iterations.
- SPX options settle to cash (European style) — no exercise risk before expiry.
- 0DTE options have extreme gamma — small moves cause large P/L swings.
