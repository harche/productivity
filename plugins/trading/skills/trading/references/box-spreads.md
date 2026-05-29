# Box Spreads

A box spread is a synthetic loan using options. The payoff at expiry is exactly the strike width, so the difference between what you pay/receive now and the width is the interest.

## Finding Strikes

Use https://www.boxtrades.com/ to find optimal strikes, expirations, and implied rates before building the spread.

## Long Box (Lending)

You pay upfront, receive strike width at expiry. Equivalent to lending money at an implied rate.

Legs: `[call@s1 BUY, call@s2 SELL, put@s1 SELL, put@s2 BUY]`

```python
s1, s2 = 7400, 7500  # strike width = 100 points = $10,000 per contract
month = "AUG26"

# Get conids for all 4 legs
c1 = get_contract(s1, "C", month)  # see options.md get_contract
c2 = get_contract(s2, "C", month)
p1 = get_contract(s1, "P", month)
p2 = get_contract(s2, "P", month)

# Build conidex: BUY c1, SELL c2, SELL p1, BUY p2
conidex = f"{SPX_CONID};;;{c1['conid']}/1,{c2['conid']}/-1,{p1['conid']}/-1,{p2['conid']}/1"
```

## Short Box (Borrowing)

You receive upfront, pay strike width at expiry. Reverse all ratios:

```python
conidex = f"{SPX_CONID};;;{c1['conid']}/-1,{c2['conid']}/1,{p1['conid']}/1,{p2['conid']}/-1"
```

## Pricing / Implied Rate

```python
width = s2 - s1  # 100
# If you pay 98.50 for a long box expiring in 90 days:
cost = 98.50
interest = width - cost  # 1.50
annualized_rate = (interest / cost) * (365 / days_to_expiry) * 100
```

## Gotchas

- **Use monthly trading class (`SPX`)** for box spreads, not weeklies (`SPXW`) — more liquidity at longer expirations. When using `/iserver/secdef/info`, check the `tradingClass` field.
- Box spreads are European-style (SPX) — no early exercise risk.
- IBKR may flag box spreads as "guaranteed to lose" if priced at exactly the width — price slightly below.
- **Always use `tif: "GTC"`** for box spread orders.
