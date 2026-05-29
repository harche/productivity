# Market Scanners

## Running a Scan

```bash
curl -sk -X POST "https://localhost:5000/v1/api/hmds/scanner" \
  -H "Content-Type: application/json" \
  -d '{"instrument": "STK", "locations": "STK.US.MAJOR", "scanCode": "TOP_PERC_GAIN", "secType": "STK", "filters": []}'
```

```python
import requests, urllib3
urllib3.disable_warnings()

BASE = "https://localhost:5000/v1/api"

results = requests.post(f"{BASE}/hmds/scanner", json={
    "instrument": "STK",
    "locations": "STK.US.MAJOR",
    "scanCode": "TOP_PERC_GAIN",
    "secType": "STK",
    "filters": []
}, verify=False).json()

for item in results.get("contracts", []):
    print(f'{item.get("symbol", "")} | {item.get("con_id", "")}')
```

## Useful Scan Codes

| scanCode | Description |
|----------|-------------|
| `TOP_PERC_GAIN` | Top % gainers |
| `TOP_PERC_LOSE` | Top % losers |
| `MOST_ACTIVE` | Most active by volume |
| `HOT_BY_VOLUME` | Unusual volume spike |
| `HIGH_DIVIDEND_YIELD_IB` | Highest dividend yield |
| `TOP_TRADE_COUNT` | Most trades |
| `TOP_TRADE_RATE` | Highest trade rate |
| `TOP_PRICE_RANGE` | Largest price range |
| `HOT_BY_PRICE_RANGE` | Unusual price range |
| `TOP_VOLUME_RATE` | Highest volume rate |
| `HIGH_VS_13W_HL` | Near 13-week high |
| `LOW_VS_13W_HL` | Near 13-week low |
| `HIGH_VS_52W_HL` | Near 52-week high |
| `LOW_VS_52W_HL` | Near 52-week low |
| `HIGH_OPT_IMP_VOLAT` | Highest option IV |
| `LOW_OPT_IMP_VOLAT` | Lowest option IV |
| `HIGH_OPT_IMP_VOLAT_OVER_HIST` | High IV vs historical (IV rank) |
| `OPT_VOLUME_MOST_ACTIVE` | Most active options |
| `HIGH_PE_RATIO` | Highest P/E ratio |
| `LOW_PE_RATIO` | Lowest P/E ratio |

## Location Codes

| locationCode | Description |
|-------------|-------------|
| `STK.US.MAJOR` | US major exchanges |
| `STK.US` | All US stocks |
| `STK.NYSE` | NYSE only |
| `STK.NASDAQ.NMS` | NASDAQ NMS |
| `STK.AMEX` | AMEX only |
| `STK.NA` | North America |
| `STK.EU` | Europe |
| `STK.TSE` | Toronto (Canadian stocks) |

## Instrument Types

`STK`, `STK.ETF.US`, `FUT.US`, `IND.US`, `BOND`.

## Filtering

```python
results = requests.post(f"{BASE}/hmds/scanner", json={
    "instrument": "STK",
    "locations": "STK.US.MAJOR",
    "scanCode": "TOP_PERC_GAIN",
    "secType": "STK",
    "filters": [
        {"code": "priceAbove", "value": 10},
        {"code": "priceBelow", "value": 500},
        {"code": "volumeAbove", "value": 1000000},
        {"code": "marketCapAbove1e6", "value": 1000}  # $1B
    ]
}, verify=False).json()
```

## Gotchas

- Scan results are a snapshot — call again for fresh results.
- Rate-limited: don't run more than a few scans per minute.
- Some scan codes only work with specific instrument/location combinations.
- Response format includes `contracts` array with `symbol`, `con_id`, and other fields.
