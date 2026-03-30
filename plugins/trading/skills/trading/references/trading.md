# Trading Reference

Raw API endpoints for placing, modifying, cancelling, and viewing orders via the IBKR Web API.

> **Session:** An authenticated brokerage session is required for all `/iserver` endpoints.
> Always check status first: `curl -sk https://localhost:5000/v1/api/iserver/auth/status`

## List Accounts (for Trading)

```bash
# Get tradeable accounts (required before placing orders)
curl -sk https://localhost:5000/v1/api/iserver/accounts | python3 -m json.tool
```

## View Orders

```bash
# Get all live orders
curl -sk https://localhost:5000/v1/api/iserver/account/orders | python3 -m json.tool

# Force refresh of live orders
curl -sk "https://localhost:5000/v1/api/iserver/account/orders?force=true" | python3 -m json.tool
```

## Place Order

**ALWAYS confirm with user before placing any order.**

```bash
curl -sk -X POST https://localhost:5000/v1/api/iserver/account/{accountId}/orders \
  -H "Content-Type: application/json" \
  -d '{
    "orders": [
      {
        "conid": 265598,
        "orderType": "LMT",
        "side": "BUY",
        "quantity": 10,
        "price": 150.00,
        "tif": "DAY"
      }
    ]
  }' | python3 -m json.tool
```

### Order Fields

| Field | Description | Required |
|---|---|---|
| `conid` | Contract ID (use `/trsrv/stocks` to find) | Yes |
| `orderType` | `MKT`, `LMT`, `STP`, `STP_LIMIT`, `MIDPRICE` | Yes |
| `side` | `BUY` or `SELL` | Yes |
| `quantity` | Number of shares/contracts | Yes |
| `price` | Limit price (required for LMT, STP_LIMIT) | Conditional |
| `auxPrice` | Stop price (required for STP, STP_LIMIT) | Conditional |
| `tif` | Time in force: `DAY`, `GTC`, `IOC`, `OPG` | Yes |
| `outsideRTH` | Allow outside regular trading hours (boolean) | No |
| `manualIndicator` | **Required for US Futures**: `true` (manual) or `false` (automated) | US Futures |

### Order Confirmation (Reply)

Order placement may return a confirmation prompt with a `replyId`. You must confirm it:

```bash
curl -sk -X POST https://localhost:5000/v1/api/iserver/reply/{replyId} \
  -H "Content-Type: application/json" \
  -d '{"confirmed": true}' | python3 -m json.tool
```

## Modify Order

**ALWAYS confirm with user before modifying any order.**

```bash
curl -sk -X POST https://localhost:5000/v1/api/iserver/account/{accountId}/order/{orderId} \
  -H "Content-Type: application/json" \
  -d '{
    "conid": 265598,
    "orderType": "LMT",
    "side": "BUY",
    "quantity": 15,
    "price": 148.00,
    "tif": "DAY"
  }' | python3 -m json.tool
```

## Cancel Order

**ALWAYS confirm with user before cancelling any order.**

```bash
curl -sk -X DELETE https://localhost:5000/v1/api/iserver/account/{accountId}/order/{orderId} \
  | python3 -m json.tool
```

## Order Types

| Type | Description |
|---|---|
| `MKT` | Market order -- executes immediately at best available price |
| `LMT` | Limit order -- executes at specified price or better |
| `STP` | Stop order -- becomes market order when stop price is reached |
| `STP_LIMIT` | Stop limit -- becomes limit order when stop price is reached |
| `MIDPRICE` | Midpoint price -- executes at midpoint between bid and ask |
| `TRAIL` | Trailing stop -- stop price trails the market |
| `TRAILLMT` | Trailing stop limit |
| `MOC` | Market on close |
| `LOC` | Limit on close |

## Time in Force

| TIF | Description |
|---|---|
| `DAY` | Good for the day only |
| `GTC` | Good till cancelled |
| `IOC` | Immediate or cancel |
| `OPG` | Market/limit on open |

## Bracket Orders

```bash
curl -sk -X POST https://localhost:5000/v1/api/iserver/account/{accountId}/orders \
  -H "Content-Type: application/json" \
  -d '{
    "orders": [
      {
        "conid": 265598,
        "orderType": "LMT",
        "side": "BUY",
        "quantity": 100,
        "price": 150.00,
        "tif": "GTC"
      },
      {
        "conid": 265598,
        "orderType": "LMT",
        "side": "SELL",
        "quantity": 100,
        "price": 160.00,
        "tif": "GTC",
        "isClose": true,
        "parentId": "PLACEHOLDER"
      },
      {
        "conid": 265598,
        "orderType": "STP",
        "side": "SELL",
        "quantity": 100,
        "auxPrice": 145.00,
        "tif": "GTC",
        "isClose": true,
        "parentId": "PLACEHOLDER"
      }
    ]
  }' | python3 -m json.tool
```

Note: The `parentId` for child orders is set automatically by the API when using the array format. The first order becomes the parent.

## Trades (Execution History)

```bash
curl -sk https://localhost:5000/v1/api/iserver/account/trades | python3 -m json.tool
```
