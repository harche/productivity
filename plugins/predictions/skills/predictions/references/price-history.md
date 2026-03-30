# Price History API Reference

## Endpoint

```bash
curl -sf "https://clob.polymarket.com/prices-history?market=CLOB_TOKEN_ID&interval=1d" | jq .
```

**Important**: The `market` param is a **CLOB Token ID** (long numeric string), NOT a condition ID. Get it from `market.clobTokenIds` — the array has two entries: `[yes_token, no_token]`.

## Parameters

| Param | Type | Description |
|---|---|---|
| `market` | string, **required** | CLOB token ID |
| `interval` | string | `1h`, `6h`, `1d`, `1w`, `1m`, `all` |
| `fidelity` | int | Granularity in minutes (default: 1) |
| `startTs` | int | Unix timestamp start |
| `endTs` | int | Unix timestamp end |

## Response

```json
{
  "history": [
    { "t": 1700000000, "p": 0.65 },
    { "t": 1700003600, "p": 0.67 }
  ]
}
```

- `t`: Unix timestamp
- `p`: Price (0-1 scale, same as outcome prices; multiply by 100 for percentage)

## Workflow: Market ID to price history

```bash
# Step 1: Get the CLOB token IDs from the market
curl -sf "https://gamma-api.polymarket.com/markets/MARKET_ID" | jq '{question, clobTokenIds}'

# Step 2: Use the first token ID (Yes token) for price history
curl -sf "https://clob.polymarket.com/prices-history?market=CLOB_TOKEN_ID&interval=1w" | jq '.history'

# Step 3: Show the last 10 data points
curl -sf "https://clob.polymarket.com/prices-history?market=CLOB_TOKEN_ID&interval=1w" | jq '.history | .[-10:]'
```
