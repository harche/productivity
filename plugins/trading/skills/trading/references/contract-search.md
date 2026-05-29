# Contract Search & Details

## Search by Symbol

```bash
curl -sk "https://localhost:5000/v1/api/trsrv/stocks?symbols=AAPL,MSFT"
```

Response is keyed by symbol. Each entry has `name`, `assetClass`, and `contracts` array:

```python
data = requests.get(f"{BASE}/trsrv/stocks?symbols=AAPL", verify=False).json()
for contract in data["AAPL"]:
    conid = contract["contracts"][0]["conid"]
    exchange = contract["contracts"][0]["exchange"]
    print(f'{contract["name"]} | conid={conid} | {exchange}')
```

**Note:** conid is nested in `contracts[0]`, not at the top level.

## Search by Name

```bash
curl -sk -X POST "https://localhost:5000/v1/api/iserver/secdef/search" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "Tesla", "secType": "STK"}'
```

Returns matching contracts with `conid`, `companyName`, `description` (exchange), and `sections` showing available derivative types (OPT, FUT, etc.).

## Futures Search

```bash
curl -sk "https://localhost:5000/v1/api/trsrv/futures?symbols=ES"
```

## Security Definition by ConID

```bash
curl -sk -X POST "https://localhost:5000/v1/api/trsrv/secdef" \
  -H "Content-Type: application/json" \
  -d '{"conids": [265598]}'
```

Returns detailed contract info including `name`, `assetClass`, `exchange`, `listingExchange`, `currency`.

## Trading Schedule

```bash
curl -sk "https://localhost:5000/v1/api/trsrv/secdef/schedule?assetClass=STK&symbol=AAPL&exchange=NASDAQ"
```

## Common ConIDs

| Symbol | ConID | Exchange | Description |
|--------|-------|----------|-------------|
| AAPL | 265598 | NASDAQ | Apple Inc |
| MSFT | 272093 | NASDAQ | Microsoft Corp |
| AMZN | 3691937 | NASDAQ | Amazon.com |
| GOOGL | 208813720 | NASDAQ | Alphabet Inc |
| SPY | 756733 | ARCA | SPDR S&P 500 ETF |
| QQQ | 320227571 | NASDAQ | Invesco QQQ Trust |
| SPX | 416904 | CBOE | S&P 500 Index |
| VIX | 13455763 | CBOE | CBOE Volatility Index |

## Gotchas

- `/trsrv/stocks` is rate-limited — don't call in a tight loop.
- Results include all exchanges and currencies — filter by `isUS: true` for US-listed.
- `secdef/search` can return bonds, warrants, and other instruments — filter by `secType` in the request body.
- `/trsrv/secdef/info` (used for options) can return transient 500 errors — retry up to 2 times.
