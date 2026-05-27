# Portfolio Greeks & Risk

## Aggregate Portfolio Greeks

Sum delta, gamma, theta, vega across all option positions, weighted by quantity.

```python
from ib_async import IB, util

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1, timeout=20)

portfolio = ib.portfolio()
opt_positions = [p for p in portfolio if p.contract.secType == 'OPT']

if not opt_positions:
    print('No option positions found.')
else:
    tickers = [ib.reqMktData(p.contract) for p in opt_positions]
    ib.sleep(5)

    net_delta = net_gamma = net_theta = net_vega = 0.0
    missing_greeks = []

    for p, t in zip(opt_positions, tickers):
        g = t.modelGreeks
        qty = p.position  # positive = long, negative = short
        c = p.contract
        label = f'{c.strike}{c.right} {c.lastTradeDateOrContractMonth}'

        if g and g.delta is not None:
            net_delta += g.delta * qty
            net_gamma += g.gamma * qty
            net_theta += g.theta * qty
            net_vega  += g.vega * qty
            print(f'  {label:>20}  qty={qty:+.0f}  d={g.delta:+.4f}  g={g.gamma:.4f}  t={g.theta:.4f}  v={g.vega:.4f}')
        else:
            missing_greeks.append(label)

    for t in tickers:
        ib.cancelMktData(t.contract)

    if missing_greeks:
        print(f'\n  Greeks unavailable for: {", ".join(missing_greeks)}')
```

## Dollar-Weighted Exposure

Translate abstract Greeks into dollar terms.

```python
# Get current SPX price for dollar weighting
from ib_async import Index
spx = ib.qualifyContracts(Index('SPX', 'CBOE'))[0]
[spx_ticker] = ib.reqTickers(spx)
ib.sleep(2)
spx_price = spx_ticker.marketPrice()

multiplier = 100  # SPX options multiplier
delta_dollars = net_delta * spx_price * multiplier
gamma_dollars = net_gamma * spx_price * multiplier
daily_theta = net_theta * multiplier
vega_dollars = net_vega * multiplier

print(f'\n--- Portfolio Risk Summary ---')
print(f'  Net Delta:     {net_delta:+.4f}  (${delta_dollars:+,.0f} per 1-pt SPX move)')
print(f'  Net Gamma:     {net_gamma:+.4f}  (${gamma_dollars:+,.0f} delta change per 1-pt move)')
print(f'  Net Theta:     {net_theta:+.4f}  (${daily_theta:+,.0f}/day premium decay)')
print(f'  Net Vega:      {net_vega:+.4f}  (${vega_dollars:+,.0f} per 1% IV change)')
print(f'  SPX Price:     {spx_price:,.2f}')
```

## Correlation-Aware Risk

Multiple SPX positions across expirations are correlated bets, not diversification. Sum total exposure.

```python
from datetime import datetime

expirations = set()
total_max_loss = 0.0
spreads = []

for p in opt_positions:
    c = p.contract
    if c.symbol == 'SPX':
        expirations.add(c.lastTradeDateOrContractMonth)

# Estimate max loss per spread from avgCost
# For credit spreads: max_loss = (wing_width - credit_received) * 100
# avgCost = cost basis per share (negative for credits)
for p in opt_positions:
    c = p.contract
    if c.symbol == 'SPX' and p.position < 0:  # short legs
        spreads.append({
            'strike': c.strike,
            'right': c.right,
            'expiry': c.lastTradeDateOrContractMonth,
            'qty': abs(p.position),
            'cost': p.avgCost,
        })

print(f'\n--- Correlation Warning ---')
print(f'  SPX expirations with open positions: {len(expirations)}')
for exp in sorted(expirations):
    days = (datetime.strptime(exp, '%Y%m%d') - datetime.now()).days
    print(f'    {exp} ({days} DTE)')
if len(expirations) > 1:
    print(f'  WARNING: {len(expirations)} overlapping SPX expirations — these are correlated.')
    print(f'  A large SPX move hits ALL of them simultaneously.')
```

## Per-Position Detail with P/L

```python
print(f'\n--- Open Option Positions ---')
print(f'  {"Contract":>30}  {"Qty":>5}  {"MktVal":>10}  {"Unrl P/L":>10}  {"Delta":>8}')
for p in portfolio:
    c = p.contract
    if c.secType != 'OPT':
        continue
    label = c.localSymbol or f'{c.symbol} {c.strike}{c.right} {c.lastTradeDateOrContractMonth}'
    pnl = p.unrealizedPNL
    print(f'  {label:>30}  {p.position:>+5.0f}  ${p.marketValue:>9,.2f}  ${pnl:>+9,.2f}')
```

## Gotchas

- Greeks are point-in-time snapshots — they change with every tick. Run this during market hours for accuracy.
- `modelGreeks` uses IBKR's pricing model, not Black-Scholes directly. Values may differ slightly from other sources.
- Gamma risk grows exponentially as expiry approaches — a flat delta with high gamma can blow up fast.
- Portfolio theta is your "daily paycheck" only if SPX stays flat. Real P/L depends on gamma exposure too.
