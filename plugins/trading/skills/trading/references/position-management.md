# Position Management: Rolling, Adjustments, Exits

## Monitor Open Positions with Greeks & DTE

```python
import requests, time, urllib3
from datetime import datetime
urllib3.disable_warnings()

BASE = "https://localhost:5000/v1/api"

# Get SPX option positions
positions = []
page = 0
while True:
    data = requests.get(f"{BASE}/portfolio/{account_id}/positions/{page}", verify=False).json()
    if not data: break
    positions.extend(data)
    if len(data) < 30: break
    page += 1

opt_positions = [p for p in positions if p.get("assetClass") == "OPT"]

# Get Greeks
conids = ",".join(str(p["conid"]) for p in opt_positions)
requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={conids}&fields=7308,7310", verify=False)
time.sleep(3)
greeks_data = requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={conids}&fields=7308,7310", verify=False).json()

def parse(val):
    if val is None: return None
    try: return float(str(val).lstrip("CHT"))
    except: return None

greeks = {item["conid"]: parse(item.get("7308")) for item in greeks_data}
```

## Detect Tested Sides

A short strike is "tested" when its delta exceeds a threshold.

```python
ROLL_THRESHOLD = 0.30

for p in opt_positions:
    qty = p["position"]
    delta = greeks.get(p["conid"])
    desc = p.get("contractDesc", "")
    
    if qty < 0 and delta is not None:
        if "P" in desc and delta < -ROLL_THRESHOLD:
            print(f"  PUT TESTED: {desc} delta={delta:.3f}")
        elif "C" in desc and delta > ROLL_THRESHOLD:
            print(f"  CALL TESTED: {desc} delta={delta:.3f}")
```

## Rolling Logic

Rolling = close the tested spread, reopen at further strikes or later expiry.

### When to roll

| Delta of short leg | Situation | Action |
|-------------------|-----------|--------|
| < 0.30 (put) or > 0.30 (call) | Comfortable | Hold |
| 0.30-0.40 | Tested | Consider rolling |
| > 0.40 | Deep trouble | Roll or close entirely |

### Roll via conidex

Build a 4-leg combo: close old spread + open new spread in one order.

```python
# Close old: BUY back short, SELL long
# Open new: SELL new short, BUY new long
roll_conidex = f"{SPX_CONID};;;{old_short_conid}/1,{old_long_conid}/-1,{new_short_conid}/-1,{new_long_conid}/1"

body = {"orders": [{
    "conidex": roll_conidex,
    "orderType": "LMT",
    "side": "BUY",
    "price": roll_price,  # negative if net credit
    "quantity": 1,
    "tif": "GTC"
}]}
```

### Roll to later expiry

Same pattern but use contracts from a different expiry month for the new legs.

## Adjustment Rules

### Add credit on the winning side

If the put side is tested, the call side has likely decayed to near-zero. Add a new call spread closer to ATM to collect additional credit.

### When to adjust vs. close

| Condition | Action | Rationale |
|-----------|--------|-----------|
| Tested delta 0.30-0.35, untested delta < 0.05 | Adjust (add credit on winning side) | New credit reduces breakeven |
| Tested delta > 0.40 | Close the whole position | SPX is trending |
| Both sides tested (whipsaw) | Close immediately | Range break |
| Already adjusted once | Close on second test | Don't compound |

## Time-Based Exit Rules

| DTE | P/L vs. Max Profit | Action | Rationale |
|-----|-------------------|--------|-----------|
| <= 21 | < 50% captured | Close | Gamma risk outweighs remaining theta |
| <= 21 | >= 50% captured | Close (take profit) | Good enough |
| <= 7 | Any profit | Close | 0DTE gamma explosion zone |
| <= 7 | Loss < 50% of max | Close (cut loss) | Risk accelerating |
| <= 1 | Any | Close regardless | Never hold SPX options into final hours |

### Close at aggregate level

For iron condors/butterflies, check total position P/L by expiry rather than individual legs.

## Smart Closing: Combo vs. Individual Legs

### Step 1: Try combo close first

Price the closing conidex via snapshot. If bid/ask spread is reasonable (< $1.00), submit as combo.

### Step 2: Fall back to individual legs

If combo has no liquidity (common after 2 PM on 0DTE):

```python
COMMISSION_PER_CONTRACT = 0.65

for p in opt_positions:
    qty = p["position"]
    price = p.get("mktPrice", 0)
    
    if qty < 0:
        # Short legs — always close (this is your risk)
        action = "BUY"
        # Submit individual closing order
    elif qty > 0:
        # Long legs — only close if value exceeds commission
        value_per_contract = abs(price) * 100
        if value_per_contract > COMMISSION_PER_CONTRACT:
            action = "SELL"
            # Submit individual closing order
        else:
            print(f"  SKIPPING: value ${value_per_contract:.2f} <= commission ${COMMISSION_PER_CONTRACT}")
```

## Gotchas

- `avgCost` from portfolio is per-share (not per-contract). Multiply by position and 100 for total.
- Rolling a tested side often results in a net debit. Only roll if the debit is small relative to remaining credit.
- Don't adjust more than once. Each adjustment adds legs and transaction costs. If the first adjustment fails, close.
- Time-based exits protect against gamma risk. A 0DTE position at 3 PM can move from +50% to -100% in minutes.
