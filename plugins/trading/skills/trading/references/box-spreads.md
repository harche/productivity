# Box Spreads

A box spread is a synthetic loan using options. The payoff at expiry is exactly the strike width, so the difference between what you pay/receive now and the width is the interest.

## Long Box (Lending)

You pay upfront, receive strike width at expiry. Equivalent to lending money at an implied rate.

```python
# Legs: [call@s1, call@s2, put@s1, put@s2]
# Actions: BUY, SELL, SELL, BUY
s1, s2 = 7400, 7500  # strike width = 100 points = $10,000 per contract
expiry = '20260820'   # ~3 months out

legs = [
    Option('SPX', expiry, s1, 'C', 'SMART', tradingClass='SPX'),
    Option('SPX', expiry, s2, 'C', 'SMART', tradingClass='SPX'),
    Option('SPX', expiry, s1, 'P', 'SMART', tradingClass='SPX'),
    Option('SPX', expiry, s2, 'P', 'SMART', tradingClass='SPX'),
]
qualified = ib.qualifyContracts(*legs)
actions = ['BUY', 'SELL', 'SELL', 'BUY']

bag = Contract(
    symbol='SPX', secType='BAG', exchange='SMART', currency='USD',
    comboLegs=[ComboLeg(conId=c.conId, ratio=1, action=a, exchange='SMART')
               for c, a in zip(qualified, actions)]
)
```

## Short Box (Borrowing)

You receive upfront, pay strike width at expiry. Equivalent to borrowing.

Reverse all actions: `['SELL', 'BUY', 'BUY', 'SELL']`

## Pricing / Implied Rate

```python
width = s2 - s1  # 100
# If you pay 98.50 for a long box expiring in 90 days:
cost = 98.50
interest = width - cost  # 1.50
annualized_rate = (interest / cost) * (365 / days_to_expiry) * 100
```

## Gotchas

- **Use monthly trading class (`SPX`)** for box spreads, not weeklies (`SPXW`) — more liquidity at longer expirations
- Box spreads are European-style (SPX) — no early exercise risk
- IBKR may flag box spreads as "guaranteed to lose" if priced at exactly the width — price slightly below
