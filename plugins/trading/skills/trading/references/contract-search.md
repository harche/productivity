# Contract Search & Details

## Search by Name or Ticker

```python
matches = ib.reqMatchingSymbols('Tesla')
for m in matches:
    c = m.contract
    print(f'{c.symbol} | {c.secType} | {c.primaryExchange} | {c.currency} | conId={c.conId}')
    if m.derivativeSecTypes:
        print(f'  Derivatives available: {m.derivativeSecTypes}')
```

Searches by ticker symbol or partial company name. Returns up to ~16 results across all exchanges and currencies.

`derivativeSecTypes` shows what's available: `['OPT', 'WAR', 'CFD', 'BAG']` etc.

## Contract Details

```python
from ib_async import Stock

aapl = ib.qualifyContracts(Stock('AAPL', 'SMART', 'USD'))[0]
details = ib.reqContractDetails(aapl)
d = details[0]

print(f'Name:       {d.longName}')        # APPLE INC
print(f'Industry:   {d.industry}')         # Technology
print(f'Category:   {d.category}')         # Computers
print(f'Subcategory:{d.subcategory}')      # Computers
print(f'Stock type: {d.stockType}')        # COMMON
print(f'Min tick:   {d.minTick}')          # 0.01
print(f'Timezone:   {d.timeZoneId}')       # US/Eastern
print(f'ISIN:       {d.secIdList}')        # [TagValue(tag='ISIN', value='US0378331005')]
```

### Trading Hours

```python
print(f'Regular:  {d.liquidHours}')
# 20260527:0930-20260527:1600;20260528:0930-20260528:1600;...

print(f'Extended: {d.tradingHours}')
# 20260527:0400-20260527:2000;20260528:0400-20260528:2000;...
```

### Valid Exchanges

```python
print(f'Exchanges: {d.validExchanges}')
# SMART,AMEX,NYSE,CBOE,ARCA,NASDAQ,IEX,BATS,...
```

## Common Use Cases

### Find a stock across exchanges

```python
matches = ib.reqMatchingSymbols('AAPL')
for m in matches:
    c = m.contract
    if c.secType == 'STK':
        print(f'{c.symbol} on {c.primaryExchange} ({c.currency})')
# AAPL on NASDAQ (USD)
# AAPL on MEXI (MXN)
# AAPL on EBS (CHF)
# AAPL on TSE (CAD)
```

### Check if options are available

```python
matches = ib.reqMatchingSymbols('SHOP')
for m in matches:
    if m.contract.secType == 'STK' and 'OPT' in (m.derivativeSecTypes or []):
        print(f'{m.contract.symbol} on {m.contract.primaryExchange} has options')
```

### Get ISIN for a stock

```python
details = ib.reqContractDetails(contract)
for tag in details[0].secIdList:
    if tag.tag == 'ISIN':
        print(f'ISIN: {tag.value}')
```

## Gotchas

- `reqMatchingSymbols` is rate-limited — don't call it in a tight loop.
- Results include bonds, warrants, and other instruments — filter by `secType == 'STK'` for stocks.
- A `conId` of `-1` means the contract isn't directly tradeable (e.g., bond placeholder).
- `reqContractDetails` can return multiple items for ambiguous contracts. Always qualify first with `qualifyContracts` to get a specific result.
