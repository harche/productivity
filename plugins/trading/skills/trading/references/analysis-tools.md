# Analysis Tools

## What-If Orders (Margin & Commission Preview)

Preview the margin impact and commission of an order without placing it:

```python
from ib_async import LimitOrder

account = ...  # from AskUserQuestion — see connection.md Multi-Account Selection
order = LimitOrder('BUY', 100, 300.0)
order.account = account            # required for multi-account setups
order.tif = 'GTC'                  # required when market is closed

state = ib.whatIfOrder(contract, order)
print(f'Margin before:  ${float(state.initMarginBefore):,.2f}')
print(f'Margin after:   ${float(state.initMarginAfter):,.2f}')
print(f'Margin change:  ${float(state.initMarginChange):,.2f}')
print(f'Commission:     ${state.commission:.4f} {state.commissionCurrency}')
```

Returns an `OrderState` with:

| Field | Description |
|-------|-------------|
| `initMarginBefore` / `After` / `Change` | Initial margin requirement |
| `maintMarginBefore` / `After` / `Change` | Maintenance margin |
| `equityWithLoanBefore` / `After` / `Change` | Equity with loan value |
| `commission` | Estimated commission |
| `commissionCurrency` | Currency of commission |

**Important:** Set `order.tif = 'GTC'` when market is closed, otherwise IB rejects DAY orders outside trading hours and returns an empty result.

## Options Math

### Implied Volatility from Price

```python
iv_result = ib.calculateImpliedVolatility(
    option_contract,
    optionPrice=50.0,
    underPrice=7500.0,
)
ib.sleep(5)
if iv_result and not isinstance(iv_result, list):
    print(f'IV: {iv_result.impliedVol:.4f}')
    print(f'Delta: {iv_result.delta:.4f}')
    print(f'Gamma: {iv_result.gamma:.6f}')
    print(f'Vega: {iv_result.vega:.4f}')
    print(f'Theta: {iv_result.theta:.4f}')
```

### Option Price from Volatility

```python
price_result = ib.calculateOptionPrice(
    option_contract,
    volatility=0.15,
    underPrice=7500.0,
)
ib.sleep(5)
if price_result and not isinstance(price_result, list):
    print(f'Theoretical price: ${price_result.optPrice:.2f}')
    print(f'Delta: {price_result.delta:.4f}')
```

**Limitations:**
- **Market hours only.** IB's pricing engine doesn't run after hours — returns empty list `[]` instead of `OptionComputation`. Always check `isinstance(result, list)` before accessing fields.
- **Error 320 with SPX options.** `ib_async` has a known bug where the default `implVolOptions=[]` parameter serializes incorrectly for index options, producing `Error 320: Please use 'Key=Value' format for Misc Options`. Stock options are unaffected.
- **Prefer `modelGreeks` for live sessions.** During market hours, `reqMktData` on an option populates `ticker.modelGreeks` with IV, delta, gamma, theta, vega automatically — no separate calculation call needed. Use `calculateImpliedVolatility`/`calculateOptionPrice` only for hypothetical what-if scenarios (different price or vol assumptions).

## Real-Time P&L

### Per Account

```python
account = ...  # from AskUserQuestion — see connection.md Multi-Account Selection
pnl = ib.reqPnL(account)
ib.sleep(2)
print(f'Daily P&L:      ${pnl.dailyPnL:,.2f}')
print(f'Unrealized P&L: ${pnl.unrealizedPnL:,.2f}')
print(f'Realized P&L:   ${pnl.realizedPnL:,.2f}')
ib.cancelPnL(account)  # always cancel when done
```

### Per Position

```python
pnl_single = ib.reqPnLSingle(account, '', conId=265598)  # AAPL conId
ib.sleep(2)
print(f'Position: {pnl_single.position}')
print(f'Daily P&L: ${pnl_single.dailyPnL:,.2f}')
print(f'Unrealized: ${pnl_single.unrealizedPnL:,.2f}')
print(f'Realized: ${pnl_single.realizedPnL:,.2f}')
print(f'Market value: ${pnl_single.value:,.2f}')
ib.cancelPnLSingle(account, '', conId=265598)
```

## Completed Orders (Order History)

```python
completed = ib.reqCompletedOrders(apiOnly=False)
for t in completed:
    o = t.order
    c = t.contract
    print(f'{c.symbol} {c.secType} | {o.action} {o.totalQuantity}x | {t.orderStatus.status}')
```

`apiOnly=True` returns only API-placed orders. `False` includes TWS/manual orders too.

**Limited history:** IB only retains completed orders for the current session (roughly 1 day). For longer history, use Flex Queries via Client Portal.

## Fundamental Data

```python
data = ib.reqFundamentalData(contract, reportType)
```

Report types: `ReportsFinSummary`, `ReportSnapshot`, `ReportsFinStatements`, `RESC` (analyst estimates), `CalendarReport`, `ReportsOwnership`.

Returns XML. **Requires IBKR fundamentals subscription** (error 10358 without it). As an alternative, use the `financial-research:company-filings` skill for SEC filings, which doesn't require an IBKR subscription.

## Gotchas

- `whatIfOrder` does NOT place the order — it's purely informational.
- `minCommission`/`maxCommission` may return `1.7e+308` (sentinel for "not applicable") — check before displaying.
- `reqPnL`/`reqPnLSingle` are streaming subscriptions — always cancel when done to avoid connection leaks.
- Options math functions need the option contract to be qualified first (`qualifyContracts`).
