# Positions, Portfolio, Closing

## Account Summary

```python
values = ib.accountValues()
base_currency = None
for v in values:
    if v.tag == 'NetLiquidation' and v.value:
        base_currency = v.currency
        break

key_tags = [
    'NetLiquidation', 'TotalCashValue', 'GrossPositionValue',
    'BuyingPower', 'AvailableFunds', 'ExcessLiquidity',
    'InitMarginReq', 'MaintMarginReq',
]
shown = set()
for tag in key_tags:
    for v in values:
        if v.tag == tag and v.currency == base_currency and tag not in shown:
            print(f'  {tag:<24} ${float(v.value):>14,.2f}')
            shown.add(tag)
```

- `accountValues()` returns ALL tags — filter by base currency to avoid duplicates
- Multi-currency accounts have separate values per currency

## List Positions

```python
positions = ib.positions()
for pos in positions:
    c = pos.contract
    print(f'{c.symbol} {c.secType} {c.strike}{c.right} pos={pos.position} avg={pos.avgCost}')
```

## Portfolio with P/L

```python
portfolio = ib.portfolio()
for p in portfolio:
    c = p.contract
    pnl = p.unrealizedPNL
    mkt_val = p.marketValue
    print(f'{c.localSymbol or c.symbol}  qty={p.position}  P/L={pnl:.2f}  mktVal={mkt_val:.2f}')
```

- `position > 0` = long (bought), `< 0` = short (sold)
- `marketPrice` may be NaN — check with `util.isNan()`
- Asset classes: `OPT`, `STK`, `FUT`, `CASH`

## Closing a Position

Reverse the action: long → SELL, short → BUY.

```python
for pos in ib.positions():
    c = pos.contract
    if c.symbol == 'SPX' and c.secType == 'OPT' and pos.position != 0:
        action = 'SELL' if pos.position > 0 else 'BUY'
        qty = abs(pos.position)
        # Get current price
        t = ib.reqMktData(c)
        ib.sleep(3)
        price = t.ask if action == 'BUY' else t.bid
        ib.cancelMktData(c)
        # Place closing order
        order = LimitOrder(action, qty, round_to_tick(price))
        trade = ib.placeOrder(c, order)
```

## Closing a Combo Position

Build a BAG with reversed actions (BUY↔SELL) from the original entry:

```python
# Original entry had: BUY lp, SELL sp, SELL sc, BUY lc
# Closing reverses:   SELL lp, BUY sp, BUY sc, SELL lc
close_bag = Contract(
    symbol='SPX', secType='BAG', exchange='SMART', currency='USD',
    comboLegs=[
        ComboLeg(conId=lp_conid, ratio=1, action='SELL', exchange='SMART'),
        ComboLeg(conId=sp_conid, ratio=1, action='BUY',  exchange='SMART'),
        ComboLeg(conId=sc_conid, ratio=1, action='BUY',  exchange='SMART'),
        ComboLeg(conId=lc_conid, ratio=1, action='SELL', exchange='SMART'),
    ]
)
```

## Open Orders

```python
orders = ib.openOrders()
trades = ib.openTrades()
for t in trades:
    o = t.order
    print(f'  OrderId={o.orderId} {o.action} {o.totalQuantity}x @ {o.lmtPrice} [{t.orderStatus.status}]')
```
