# Market Scanners

## Running a Scan

```python
from ib_async import ScannerSubscription

sub = ScannerSubscription(
    instrument='STK',
    locationCode='STK.US.MAJOR',
    scanCode='TOP_PERC_GAIN',
    numberOfRows=10,
)
results = ib.reqScannerData(sub)
for r in results:
    c = r.contractDetails.contract
    name = r.contractDetails.longName
    print(f'{r.rank}: {c.symbol:6} | {name}')
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
| `HIGH_OPT_IMP_VOLAT` | Highest option implied volatility |
| `LOW_OPT_IMP_VOLAT` | Lowest option implied volatility |
| `HIGH_OPT_IMP_VOLAT_OVER_HIST` | High IV vs historical (IV rank) |
| `OPT_VOLUME_MOST_ACTIVE` | Most active options |
| `HIGH_PE_RATIO` | Highest P/E ratio |
| `LOW_PE_RATIO` | Lowest P/E ratio |

There are **477 scan types** total. To see all of them:

```python
import xml.etree.ElementTree as ET
xml = ib.reqScannerParameters()
root = ET.fromstring(xml)
for st in root.findall('.//ScanType'):
    code = st.findtext('scanCode', '')
    name = st.findtext('displayName', '')
    print(f'{code}: {name}')
```

## Location Codes

| locationCode | Description |
|-------------|-------------|
| `STK.US.MAJOR` | US major exchanges |
| `STK.US` | All US stocks |
| `STK.US.MINOR` | US minor exchanges |
| `STK.NA` | North America |
| `STK.EU` | Europe |
| `STK.AMEX` | AMEX only |
| `STK.NYSE` | NYSE only |
| `STK.NASDAQ.NMS` | NASDAQ NMS |
| `STK.NASDAQ.SCM` | NASDAQ SmallCap |
| `STK.TSE` | Toronto (Canadian stocks) |

## Instrument Types

`STK`, `STK.ETF.US` (US equity ETFs), `STK.ETF.FI.US` (US fixed income ETFs), `FUT.US` (US futures), `IND.US` (US indexes), `BOND` (corporate bonds).

## Filtering

```python
sub = ScannerSubscription(
    instrument='STK',
    locationCode='STK.US.MAJOR',
    scanCode='TOP_PERC_GAIN',
    numberOfRows=20,
    abovePrice=10.0,          # min price
    belowPrice=500.0,         # max price
    aboveVolume=1000000,      # min average volume
    marketCapAbove=1e9,       # min market cap ($1B)
)
```

## Gotchas

- `longName` may be empty in scan results — use the contract symbol as fallback.
- Scan results are a snapshot; they don't update automatically. Call `reqScannerData` again for fresh results.
- Rate-limited: don't run more than a few scans per minute.
- Some scan codes only work with specific instrument/location combinations.
- `reqScannerParameters` returns a ~1.7MB XML — parse it, don't print it.
