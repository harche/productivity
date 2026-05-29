# Orders: Placement, Combos, Brackets

## NEVER use MKT for options. Always LMT.

## Single Contract Order

```python
from ib_async import LimitOrder
order = LimitOrder('BUY', 10, 150.00)
trade = ib.placeOrder(contract, order)
ib.sleep(30)  # wait for fill
print(f'Status: {trade.orderStatus.status}, Filled: {trade.filled()}')
```

## Combo (BAG) Contracts

A BAG contract bundles multiple legs into one order. IBKR prices and fills it as a unit.

```python
from ib_async import Contract, ComboLeg

bag = Contract(
    symbol='SPX',
    secType='BAG',
    exchange='SMART',
    currency='USD',
    comboLegs=[
        ComboLeg(conId=long_put.conId,   ratio=1, action='BUY',  exchange='SMART'),
        ComboLeg(conId=short_put.conId,  ratio=1, action='SELL', exchange='SMART'),
        ComboLeg(conId=short_call.conId, ratio=1, action='SELL', exchange='SMART'),
        ComboLeg(conId=long_call.conId,  ratio=1, action='BUY',  exchange='SMART'),
    ]
)
```

- **Leg order matters** — convention: Long Put, Short Put, Short Call, Long Call
- **Ratio is always 1** — quantity goes on the order, not the legs
- **Actions are per-leg**: independent of the overall order direction
- **For closing**, reverse all actions: BUY→SELL, SELL→BUY

## Combo Pricing

Combo bid/ask is the **spread price**, not individual legs:

```python
ticker = ib.reqMktData(bag, '', False, False)
ib.sleep(8)  # combos need 6-8s to populate — 3s returns NaN
combo_bid = ticker.bid   # what you'd receive selling
combo_ask = ticker.ask   # what you'd pay buying
ib.cancelMktData(bag)
```

**Negative prices are normal** for credit spreads — they represent money received.

## Submitting a Combo Order

**Always use `tif='GTC'`** — the gateway may override DAY orders and reject them with error 10349.

```python
# Credit spread: you're "buying" a combo that pays you credit
# Entry price is negative (you receive money)
entry_price = round_to_tick(combo_ask)  # use ask for entry
order = LimitOrder('BUY', quantity, entry_price, tif='GTC')
trade = ib.placeOrder(bag, order)
```

## Bracket Orders (Parent + Profit Target + Stop-Loss)

```python
import time

# 1. Entry (parent) — don't transmit yet
entry = LimitOrder('BUY', 1, entry_price)
entry.transmit = False
entry_trade = ib.placeOrder(bag, entry)

# 2. Profit target (child) — transmit triggers parent
profit = LimitOrder('SELL', 1, profit_price)
profit.parentId = entry.orderId
profit.transmit = True
ib.placeOrder(bag, profit)
```

- **Parent must have `transmit=False`** initially
- **Child's `transmit=True` triggers parent transmission**
- `parentId` is the orderId assigned after `placeOrder()` returns

## OCA Groups (One-Cancels-All)

Link profit target and stop-loss so one cancels the other:

```python
oca_group = f'oca_SPX_{int(time.time())}'

profit_order = LimitOrder('SELL', 1, profit_price)
profit_order.ocaGroup = oca_group
profit_order.ocaType = 1  # cancel others when this fills
ib.placeOrder(bag, profit_order)

stop_order = Order()
stop_order.action = 'SELL'
stop_order.totalQuantity = 1
stop_order.orderType = 'STP LMT'
stop_order.auxPrice = stop_trigger  # stop trigger price
stop_order.lmtPrice = stop_limit    # limit after triggered
stop_order.ocaGroup = oca_group
stop_order.ocaType = 1
ib.placeOrder(bag, stop_order)
```

## Cancel & Modify

```python
# Cancel
ib.cancelOrder(trade.order)

# Modify price
trade.order.lmtPrice = new_price
ib.placeOrder(trade.contract, trade.order)

# List open orders
orders = ib.openOrders()
trades = ib.openTrades()
```

## Wait for Fill

```python
def wait_for_fill(ib, trade, timeout=40):
    for _ in range(timeout):
        ib.sleep(1)
        if trade.orderStatus.status == 'Filled':
            return True
    return False
```

## What-If Margin

Use `ib.whatIfOrder()` — it returns margin impact without placing an order:

```python
order = LimitOrder('BUY', 1, entry_price, tif='GTC')
margin = ib.whatIfOrder(contract, order)
ib.sleep(3)
print(f'Init Margin:  {margin.initMarginChange}')
print(f'Maint Margin: {margin.maintMarginChange}')
print(f'Equity:       {margin.equityWithLoanChange}')
```

- **Use `tif='GTC'`** — the gateway may override DAY orders and reject them (error 10349)
- Works with BAG/combo contracts
- Works outside market hours
- No need to cancel — `whatIfOrder` doesn't place a real order
