# Market Data

Retrieve market data snapshots, historical data, search contracts, and run scanners.

> **Session:** An authenticated brokerage session is required for all market data endpoints.

## Contract Search

```bash
# Search stock contracts by symbol
curl -sk "https://localhost:5000/v1/api/trsrv/stocks?symbols=AAPL" | python3 -m json.tool

# Search multiple symbols
curl -sk "https://localhost:5000/v1/api/trsrv/stocks?symbols=AAPL,MSFT,GOOGL" | python3 -m json.tool

# Search futures contracts
curl -sk "https://localhost:5000/v1/api/trsrv/futures?symbols=ES" | python3 -m json.tool

# Get security definitions by contract IDs
curl -sk -X POST https://localhost:5000/v1/api/trsrv/secdef \
  -H "Content-Type: application/json" \
  -d '{"conids": [265598, 272093]}' | python3 -m json.tool

# Get trading schedule for a symbol
curl -sk "https://localhost:5000/v1/api/trsrv/secdef/schedule?assetClass=STK&symbol=AAPL" | python3 -m json.tool
```

**Common Contract IDs (conids):**

| Symbol | ConID | Description |
|---|---|---|
| AAPL | 265598 | Apple Inc. |
| MSFT | 272093 | Microsoft Corp. |
| AMZN | 3691937 | Amazon.com Inc. |
| GOOGL | 208813720 | Alphabet Inc. |
| SPY | 756733 | SPDR S&P 500 ETF |
| QQQ | 320227571 | Invesco QQQ Trust |

Use `/trsrv/stocks` to look up conids for any symbol. The response nests conid inside `contracts`:

```json
{
    "AAPL": [
        {
            "name": "APPLE INC",
            "assetClass": "STK",
            "contracts": [
                { "conid": 265598, "exchange": "NASDAQ", "isUS": true }
            ]
        }
    ]
}
```

Extract conid via: `data['SYMBOL'][0]['contracts'][0]['conid']`

## Market Data Snapshot

**PREREQUISITE:** You MUST call `/iserver/accounts` at least once per session before market data snapshots will work. Without this, snapshots return conid-only responses with no price fields.

**IMPORTANT:** Use the `/iserver/marketdata/snapshot` endpoint (NOT `/md/snapshot`). The `/md/snapshot` endpoint may not return field values reliably.

```bash
# REQUIRED: Initialize iserver session first (call once per session)
curl -sk https://localhost:5000/v1/api/iserver/accounts | python3 -m json.tool

# Get snapshot for one or more contracts
# First call primes the subscription (may return empty fields) — wait 2-3 seconds, then call again
curl -sk "https://localhost:5000/v1/api/iserver/marketdata/snapshot?conids=265598&fields=31,55,84,86" | python3 -m json.tool
sleep 3
curl -sk "https://localhost:5000/v1/api/iserver/marketdata/snapshot?conids=265598&fields=31,55,84,86" | python3 -m json.tool

# Multiple contracts
curl -sk "https://localhost:5000/v1/api/iserver/marketdata/snapshot?conids=265598,272093&fields=31,55,84,86,70,71,82,83,7295" | python3 -m json.tool
```

**Note:** The first snapshot call for a contract primes the data subscription and will return incomplete data (conid only, no price fields). You MUST call it again after a 2-3 second pause to get populated fields. This two-call pattern is required for every new conid you query.

### Common Snapshot Fields

| Field ID | Description |
|---|---|
| 31 | Last price |
| 55 | Symbol |
| 70 | High |
| 71 | Low |
| 82 | Change |
| 83 | Change % |
| 84 | Bid price |
| 85 | Ask size |
| 86 | Ask price |
| 87 | Volume |
| 88 | Bid size |
| 7295 | Open price |
| 7296 | Close price |
| 7674 | EPS |
| 7675 | Market cap |
| 7676 | P/E ratio |
| 7677 | 52-week high |
| 7678 | 52-week low |
| 7679 | Dividend yield |

## Historical Data

```bash
# Get historical candlestick data
curl -sk -X POST https://localhost:5000/v1/api/hmds/history \
  -H "Content-Type: application/json" \
  -d '{"conid": 265598, "period": "1d", "bar": "1h"}' | python3 -m json.tool

# Weekly bars for 1 year
curl -sk -X POST https://localhost:5000/v1/api/hmds/history \
  -H "Content-Type: application/json" \
  -d '{"conid": 265598, "period": "1y", "bar": "1w"}' | python3 -m json.tool

# Include outside regular trading hours
curl -sk -X POST https://localhost:5000/v1/api/hmds/history \
  -H "Content-Type: application/json" \
  -d '{"conid": 265598, "period": "5d", "bar": "15min", "outsideRth": true}' | python3 -m json.tool
```

### Period Values

| Value | Description |
|---|---|
| `1min` - `30min` | Minutes |
| `1h` - `8h` | Hours |
| `1d` - `5d` | Days |
| `1w` - `4w` | Weeks |
| `1m` - `12m` | Months |
| `1y` - `5y` | Years |

### Bar Sizes

| Value | Description |
|---|---|
| `1min` | 1 minute bars |
| `2min` | 2 minute bars |
| `3min` | 3 minute bars |
| `5min` | 5 minute bars |
| `10min` | 10 minute bars |
| `15min` | 15 minute bars |
| `30min` | 30 minute bars |
| `1h` | 1 hour bars |
| `2h` | 2 hour bars |
| `4h` | 4 hour bars |
| `8h` | 8 hour bars |
| `1d` | 1 day bars |
| `1w` | 1 week bars |
| `1m` | 1 month bars |

## Market Scanner

```bash
# Run a market scanner
curl -sk -X POST https://localhost:5000/v1/api/hmds/scanner \
  -H "Content-Type: application/json" \
  -d '{
    "instrument": "STK",
    "locations": "STK.US.MAJOR",
    "scanCode": "TOP_PERC_GAIN",
    "secType": "STK",
    "filters": []
  }' | python3 -m json.tool
```

### Common Scan Codes

| Code | Description |
|---|---|
| `TOP_PERC_GAIN` | Top % gainers |
| `TOP_PERC_LOSE` | Top % losers |
| `MOST_ACTIVE` | Most active by volume |
| `HOT_BY_VOLUME` | Hot by volume |
| `TOP_TRADE_COUNT` | Top trade count |
| `TOP_TRADE_RATE` | Top trade rate |
| `TOP_PRICE_RANGE` | Top price range |
| `HOT_BY_PRICE` | Hot by price |
| `HIGH_DIVIDEND_YIELD_IB` | High dividend yield |
| `TOP_OPEN_PERC_GAIN` | Top open % gain |
| `TOP_OPEN_PERC_LOSE` | Top open % loss |

### Scanner Locations

| Location | Description |
|---|---|
| `STK.US.MAJOR` | US major exchanges |
| `STK.US` | All US exchanges |
| `STK.US.MINOR` | US minor exchanges |
| `STK.EU` | European exchanges |
| `STK.AMEX` | AMEX |
| `STK.NYSE` | NYSE |
| `STK.NASDAQ` | NASDAQ |
