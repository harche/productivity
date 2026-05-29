# Positions, Portfolio, Closing

## Account Summary

```bash
curl -sk "https://localhost:5000/v1/api/portfolio/ACCOUNT_ID/summary"
```

Key fields in response: `netliquidation`, `totalcashvalue`, `grosspositionvalue`, `buyingpower`, `availablefunds`, `excessliquidity`, `initmarginreq`, `maintmarginreq`.

Each field has `amount`, `currency`, `isNull`, `severity`, `timestamp`.

## List Positions

Positions are paginated — 30 per page, starting at page 0:

```bash
curl -sk "https://localhost:5000/v1/api/portfolio/ACCOUNT_ID/positions/0"
```

Fetch all pages:

```python
import requests, urllib3
urllib3.disable_warnings()

BASE = "https://localhost:5000/v1/api"

def get_all_positions(account_id):
    positions = []
    page = 0
    while True:
        data = requests.get(f"{BASE}/portfolio/{account_id}/positions/{page}", verify=False).json()
        if not data:
            break
        positions.extend(data)
        if len(data) < 30:
            break
        page += 1
    return positions
```

Position fields: `conid`, `contractDesc`, `position`, `mktPrice`, `mktValue`, `avgCost`, `unrealizedPnl`, `assetClass` (`STK`, `OPT`, `FUT`, `CASH`).

## Force Cache Refresh

If positions seem stale:

```bash
curl -sk -X POST "https://localhost:5000/v1/api/portfolio/ACCOUNT_ID/positions/invalidate"
```

## Portfolio with P/L

```python
positions = get_all_positions(account_id)
for p in positions:
    desc = p.get("contractDesc", "")
    qty = p.get("position", 0)
    pnl = p.get("unrealizedPnl", 0)
    mkt_val = p.get("mktValue", 0)
    print(f"{desc}  qty={qty}  P/L={pnl:.2f}  mktVal={mkt_val:.2f}")
```

- `position > 0` = long (bought), `< 0` = short (sold)

## Closing a Position

Reverse the action: long → SELL, short → BUY.

```python
action = "SELL" if position > 0 else "BUY"
qty = abs(position)
body = {"orders": [{
    "conid": conid,
    "orderType": "LMT",
    "side": action,
    "price": limit_price,
    "quantity": qty,
    "tif": "DAY"
}]}
```

## Closing a Combo Position

Reverse all conidex ratios:

```python
# Original entry: "416904;;;conid1/1,conid2/-1,conid3/-1,conid4/1"
# Closing:        "416904;;;conid1/-1,conid2/1,conid3/1,conid4/-1"

def reverse_conidex(conidex):
    prefix, legs = conidex.split(";;;")
    reversed_legs = []
    for leg in legs.split(","):
        conid, ratio = leg.rsplit("/", 1)
        new_ratio = str(-int(ratio))
        reversed_legs.append(f"{conid}/{new_ratio}")
    return f"{prefix};;;{','.join(reversed_legs)}"
```

## Trade History

```bash
curl -sk https://localhost:5000/v1/api/iserver/account/trades
```

Returns recent executions with `symbol`, `side`, `price`, `size`, `time`.

## Open Orders

```bash
curl -sk https://localhost:5000/v1/api/iserver/account/orders
```

## Gotchas

- Positions are paginated — always check if more pages exist.
- `avgCost` is per-share (not per-contract). Multiply by position and 100 for total cost basis.
- For combo (BAG) entries, IBKR may report `avgCost` per-leg or per-combo depending on fill. Verify against trade confirmations.
- Call `/portfolio/accounts` before accessing `/portfolio/{accountId}/...` endpoints.
