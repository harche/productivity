# Orders: Placement, Combos, Brackets

## NEVER use MKT for options. Always LMT.

## Single Contract Order

```python
import requests, urllib3
urllib3.disable_warnings()

BASE = "https://localhost:5000/v1/api"
account_id = "U8265837"

body = {"orders": [{
    "conid": 265598,
    "orderType": "LMT",
    "side": "BUY",
    "price": 150.00,
    "quantity": 10,
    "tif": "DAY"
}]}

resp = requests.post(f"{BASE}/iserver/account/{account_id}/orders",
                     json=body, verify=False).json()
```

## Confirmation Chain

Order responses may require confirmation. If the response contains a `replyId`, confirm it:

```python
def submit_with_confirmation(account_id, order_body, max_confirms=5):
    resp = requests.post(f"{BASE}/iserver/account/{account_id}/orders",
                         json=order_body, verify=False).json()
    
    for _ in range(max_confirms):
        if not isinstance(resp, list):
            break
        item = resp[0]
        
        if "order_id" in item or "orderId" in item:
            order_id = item.get("order_id") or item.get("orderId")
            return order_id
        
        if "id" in item:  # replyId confirmation needed
            reply_id = item["id"]
            resp = requests.post(f"{BASE}/iserver/reply/{reply_id}",
                                 json={"confirmed": True}, verify=False).json()
            continue
        break
    
    return None
```

## Combo Orders (conidex)

Combos use the `conidex` format instead of `conid`:

```
"underlyingConid;;;legConid1/ratio1,legConid2/ratio2,..."
```

Positive ratio = BUY, negative = SELL.

```python
# Iron butterfly: BUY long put, SELL short put, SELL short call, BUY long call
conidex = f"416904;;;{lp_conid}/1,{sp_conid}/-1,{sc_conid}/-1,{lc_conid}/1"

body = {"orders": [{
    "conidex": conidex,
    "orderType": "LMT",
    "side": "BUY",
    "price": -72.20,  # negative = credit received
    "quantity": 1,
    "tif": "GTC"  # REQUIRED for combos
}]}
```

- **Leg order**: Long Put, Short Put, Short Call, Long Call
- **Always use `tif: "GTC"` for combos** — DAY orders may be rejected (error 10349)
- **Negative prices are normal** for credit spreads — you receive money
- **For closing**, reverse all ratios: `/1` becomes `/-1` and vice versa

## Bracket Orders

Submit as an array of 3 orders. Child orders reference the parent:

```python
body = {"orders": [
    {  # Parent: entry
        "conid": 265598,
        "orderType": "LMT",
        "side": "BUY",
        "price": 150.00,
        "quantity": 1,
        "tif": "DAY"
    },
    {  # Child: profit target
        "conid": 265598,
        "orderType": "LMT",
        "side": "SELL",
        "price": 165.00,
        "quantity": 1,
        "tif": "GTC",
        "parentId": "PLACEHOLDER",
        "isClose": True
    },
    {  # Child: stop-loss
        "conid": 265598,
        "orderType": "STP",
        "side": "SELL",
        "price": 140.00,
        "quantity": 1,
        "tif": "GTC",
        "parentId": "PLACEHOLDER",
        "isClose": True
    }
]}
```

## Order Types

| orderType | Description |
|-----------|-------------|
| `LMT` | Limit |
| `MKT` | Market (NEVER for options) |
| `STP` | Stop |
| `STP_LIMIT` | Stop limit (`price` = limit, `auxPrice` = stop trigger) |
| `MIDPRICE` | Midpoint |
| `TRAIL` | Trailing stop |
| `MOC` | Market on close |
| `LOC` | Limit on close |

## Cancel & Modify

```bash
# Cancel
curl -sk -X DELETE "https://localhost:5000/v1/api/iserver/account/ACCOUNT_ID/order/ORDER_ID"

# Modify
curl -sk -X POST "https://localhost:5000/v1/api/iserver/account/ACCOUNT_ID/order/ORDER_ID" \
  -H "Content-Type: application/json" \
  -d '{"price": 155.00, "quantity": 10}'
```

## List Open Orders

```bash
curl -sk https://localhost:5000/v1/api/iserver/account/orders
```

## Poll for Fill

```bash
curl -sk "https://localhost:5000/v1/api/iserver/account/order/status/ORDER_ID"
```

Check `status` field: `Submitted`, `Filled`, `Cancelled`, `Inactive`.

## Gotchas

- Always handle the confirmation chain — most orders return at least one `replyId`.
- `conidex` and `conid` are mutually exclusive — use one or the other.
- Order `side` is the overall direction: `BUY` to open a credit spread (you receive the combo).
- Modify response also requires confirmation chain handling.
