# Position Management: Rolling, Adjustments, Exits

## Monitor Open Positions with Greeks & DTE

```python
from ib_async import IB, util
from datetime import datetime

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1, timeout=20)

portfolio = ib.portfolio()
opt_positions = [p for p in portfolio if p.contract.secType == 'OPT' and p.contract.symbol == 'SPX']

if not opt_positions:
    print('No SPX option positions.')
else:
    tickers = [ib.reqMktData(p.contract) for p in opt_positions]
    ib.sleep(5)

    print(f'{"Contract":>30}  {"Qty":>5}  {"Delta":>8}  {"P/L":>10}  {"DTE":>5}')
    for p, t in zip(opt_positions, tickers):
        c = p.contract
        label = f'{c.strike}{c.right} {c.lastTradeDateOrContractMonth}'
        g = t.modelGreeks
        delta = f'{g.delta:+.4f}' if g and g.delta is not None else '  N/A'
        dte = (datetime.strptime(c.lastTradeDateOrContractMonth, '%Y%m%d') - datetime.now()).days
        print(f'{label:>30}  {p.position:>+5.0f}  {delta:>8}  ${p.unrealizedPNL:>+9,.2f}  {dte:>5}')

    for t in tickers:
        ib.cancelMktData(t.contract)
```

## Detect Tested Sides

A short strike is "tested" when its delta exceeds a threshold — meaning SPX has moved close enough that the probability of expiring ITM has increased significantly.

```python
ROLL_THRESHOLD = 0.30  # delta magnitude

tested_legs = []
for p, t in zip(opt_positions, tickers):
    c = p.contract
    g = t.modelGreeks
    if p.position < 0 and g and g.delta is not None:  # short legs only
        if c.right == 'P' and g.delta < -ROLL_THRESHOLD:
            tested_legs.append((p, t, 'put'))
            print(f'  PUT TESTED: {c.strike}P delta={g.delta:.3f} (threshold: {-ROLL_THRESHOLD})')
        elif c.right == 'C' and g.delta > ROLL_THRESHOLD:
            tested_legs.append((p, t, 'call'))
            print(f'  CALL TESTED: {c.strike}C delta={g.delta:.3f} (threshold: {+ROLL_THRESHOLD})')

if not tested_legs:
    print('  No sides tested — position is within range.')
```

## Rolling Logic

Rolling = close the tested spread, reopen at further strikes or a later expiry to give the position more room.

### When to roll

| Delta of short leg | Situation | Action |
|-------------------|-----------|--------|
| < 0.30 (put) or > 0.30 (call) | Comfortable | Hold |
| 0.30-0.40 | Tested | Consider rolling |
| > 0.40 | Deep trouble | Roll or close entirely |

### Roll to further strikes (same expiry)

```python
from ib_async import Option, Contract, ComboLeg, LimitOrder

# Example: short 7400P is tested, roll down to 7350P
# Assumes you have the tested leg and its paired long leg identified
old_short_strike = 7400
new_short_strike = 7350  # further OTM
old_long_strike = 7370   # existing wing
new_long_strike = 7320   # new wing (maintain same width)

# Qualify all four legs
old_short = ib.qualifyContracts(Option('SPX', expiry, old_short_strike, 'P', 'SMART', tradingClass=tc))[0]
old_long  = ib.qualifyContracts(Option('SPX', expiry, old_long_strike, 'P', 'SMART', tradingClass=tc))[0]
new_short = ib.qualifyContracts(Option('SPX', expiry, new_short_strike, 'P', 'SMART', tradingClass=tc))[0]
new_long  = ib.qualifyContracts(Option('SPX', expiry, new_long_strike, 'P', 'SMART', tradingClass=tc))[0]

# Build the roll as a single 4-leg combo:
# Close old spread (buy back short, sell long) + open new spread (sell new short, buy new long)
roll_bag = Contract(
    symbol='SPX', secType='BAG', exchange='SMART', currency='USD',
    comboLegs=[
        ComboLeg(conId=old_short.conId, ratio=1, action='BUY',  exchange='SMART'),  # close short
        ComboLeg(conId=old_long.conId,  ratio=1, action='SELL', exchange='SMART'),  # close long
        ComboLeg(conId=new_short.conId, ratio=1, action='SELL', exchange='SMART'),  # open short
        ComboLeg(conId=new_long.conId,  ratio=1, action='BUY',  exchange='SMART'),  # open long
    ]
)

# Price the roll
roll_ticker = ib.reqMktData(roll_bag)
ib.sleep(3)

def valid_price(val):
    if util.isNan(val) or val == -1:
        return None
    return val

roll_bid = valid_price(roll_ticker.bid)
roll_ask = valid_price(roll_ticker.ask)
ib.cancelMktData(roll_bag)

print(f'Roll {old_short_strike}P→{new_short_strike}P:')
print(f'  Bid: {roll_bid}  Ask: {roll_ask}')
if roll_bid and roll_bid < 0:
    print(f'  Net credit: ${abs(roll_bid) * 100:,.0f} (you receive money)')
elif roll_ask and roll_ask > 0:
    print(f'  Net debit: ${roll_ask * 100:,.0f} (you pay money)')
```

### Roll to later expiry

Same pattern but use a different `expiry` for the new legs. Rolling out in time collects additional theta but extends your risk window.

```python
new_expiry = '20260603'  # next week
new_short = ib.qualifyContracts(Option('SPX', new_expiry, new_short_strike, 'P', 'SMART', tradingClass=tc))[0]
new_long  = ib.qualifyContracts(Option('SPX', new_expiry, new_long_strike, 'P', 'SMART', tradingClass=tc))[0]
# Then build the same 4-leg roll_bag as above
```

## Adjustment Rules

### Add credit on the winning side

If the put side is tested, the call side has likely decayed to near-zero. Add a new call spread closer to ATM to collect additional credit, reducing your overall risk.

```python
# Check if untested side has decayed
for p, t in zip(opt_positions, tickers):
    c = p.contract
    g = t.modelGreeks
    if p.position < 0 and g and g.delta is not None:
        if c.right == 'C' and abs(g.delta) < 0.05:
            print(f'  Call side {c.strike}C delta={g.delta:.3f} — nearly worthless, good candidate for adjustment')
```

### When to adjust vs. close

| Condition | Action | Rationale |
|-----------|--------|-----------|
| Tested delta 0.30-0.35, untested delta < 0.05 | Adjust (add credit on winning side) | New credit reduces breakeven |
| Tested delta > 0.40 | Close the whole position | SPX is trending, more exposure = more risk |
| Both sides tested (whipsaw) | Close immediately | You're caught in a range break |
| Already adjusted once | Close on second test | Don't compound — take the loss |

### Execute the adjustment

```python
# Example: put side tested, add a tighter call spread
# Find new call strikes closer to ATM
adj_short_call_strike = round_to_strike(spx_price + 10)  # 10 points OTM
adj_long_call_strike = adj_short_call_strike + 30  # 30-point wing

adj_sc = ib.qualifyContracts(Option('SPX', expiry, adj_short_call_strike, 'C', 'SMART', tradingClass=tc))[0]
adj_lc = ib.qualifyContracts(Option('SPX', expiry, adj_long_call_strike, 'C', 'SMART', tradingClass=tc))[0]

adj_bag = Contract(
    symbol='SPX', secType='BAG', exchange='SMART', currency='USD',
    comboLegs=[
        ComboLeg(conId=adj_sc.conId, ratio=1, action='SELL', exchange='SMART'),
        ComboLeg(conId=adj_lc.conId, ratio=1, action='BUY',  exchange='SMART'),
    ]
)

adj_ticker = ib.reqMktData(adj_bag)
ib.sleep(3)
adj_credit = valid_price(adj_ticker.bid)
ib.cancelMktData(adj_bag)

if adj_credit:
    print(f'Adjustment credit: ${abs(adj_credit) * 100:,.0f}')
    print(f'New call spread: {adj_short_call_strike}C / {adj_long_call_strike}C')
```

## Time-Based Exit Rules

### Decision table

| DTE | P/L vs. Max Profit | Action | Rationale |
|-----|-------------------|--------|-----------|
| <= 21 | < 50% captured | Close | Gamma risk outweighs remaining theta |
| <= 21 | >= 50% captured | Close (take profit) | Good enough, don't push it |
| <= 7 | Any profit | Close | 0DTE gamma explosion zone |
| <= 7 | Loss < 50% of max | Close (cut loss) | Risk of larger loss accelerating |
| <= 1 | Any | Close regardless | Never hold SPX options into final hours |

### Calculate DTE and P/L percentage

```python
from datetime import datetime

for p in opt_positions:
    c = p.contract
    expiry_date = datetime.strptime(c.lastTradeDateOrContractMonth, '%Y%m%d')
    dte = (expiry_date - datetime.now()).days

    # avgCost is per-share cost basis (negative for credits received)
    entry_credit_per_share = abs(p.avgCost / 100)  # convert from total to per-share
    current_value = abs(p.marketValue / (abs(p.position) * 100)) if p.position != 0 else 0

    # For short positions: profit = entry_credit - current_value
    if p.position < 0:
        pnl_pct = (1 - current_value / entry_credit_per_share) * 100 if entry_credit_per_share > 0 else 0
        print(f'  {c.strike}{c.right} {c.lastTradeDateOrContractMonth}: DTE={dte}, P/L={pnl_pct:.0f}% of max')

        if dte <= 1:
            print(f'    ACTION: CLOSE — expiry imminent')
        elif dte <= 7 and pnl_pct > 0:
            print(f'    ACTION: CLOSE — take profit before gamma zone')
        elif dte <= 21 and pnl_pct < 50:
            print(f'    ACTION: CLOSE — insufficient profit for remaining risk')
```

### Close at aggregate level

For iron condors/butterflies, check the total position P/L rather than individual legs:

```python
# Group positions by expiry to assess the full spread
from collections import defaultdict

by_expiry = defaultdict(list)
for p in opt_positions:
    c = p.contract
    by_expiry[c.lastTradeDateOrContractMonth].append(p)

for exp, positions in by_expiry.items():
    total_pnl = sum(p.unrealizedPNL for p in positions)
    total_cost = sum(abs(p.avgCost * p.position) for p in positions)
    dte = (datetime.strptime(exp, '%Y%m%d') - datetime.now()).days

    print(f'\nExpiry {exp} ({dte} DTE):')
    print(f'  Total P/L: ${total_pnl:+,.2f}')
    print(f'  Total cost basis: ${total_cost:,.2f}')
    if total_cost > 0:
        pnl_pct = (total_pnl / total_cost) * 100
        print(f'  Return: {pnl_pct:+.1f}%')
```

## Smart Closing: Late-Day Liquidity Fallback

Combo close orders work well in the morning but often can't fill after ~2 PM on 0DTE — market makers pull back on multi-leg orders. Check combo liquidity first, and fall back to closing legs individually.

### Step 1: Check combo liquidity

```python
from ib_async import Contract, ComboLeg, LimitOrder, util

# Build the closing combo (reverse actions from entry)
close_bag = Contract(
    symbol='SPX', secType='BAG', exchange='SMART', currency='USD',
    comboLegs=[
        ComboLeg(conId=lp_conid, ratio=1, action='SELL', exchange='SMART'),
        ComboLeg(conId=sp_conid, ratio=1, action='BUY',  exchange='SMART'),
        ComboLeg(conId=sc_conid, ratio=1, action='BUY',  exchange='SMART'),
        ComboLeg(conId=lc_conid, ratio=1, action='SELL', exchange='SMART'),
    ]
)

combo_ticker = ib.reqMktData(close_bag)
ib.sleep(3)

combo_bid = combo_ticker.bid
combo_ask = combo_ticker.ask
ib.cancelMktData(close_bag)

has_liquidity = True
if util.isNan(combo_bid) or combo_bid == -1 or util.isNan(combo_ask) or combo_ask == -1:
    has_liquidity = False
    print('Combo has no bid/ask — no liquidity, skipping combo order')
elif abs(combo_ask - combo_bid) > 1.00:
    has_liquidity = False
    print(f'Combo spread too wide: bid={combo_bid} ask={combo_ask} (${abs(combo_ask - combo_bid):.2f}) — skipping combo order')
else:
    print(f'Combo liquidity OK: bid={combo_bid} ask={combo_ask}')
```

### Step 2a: If combo has liquidity — close as combo

```python
if has_liquidity:
    close_price = round_to_tick(combo_ask)
    order = LimitOrder('BUY', quantity, close_price)
    trade = ib.placeOrder(close_bag, order)
```

### Step 2b: If no combo liquidity — close short legs individually, evaluate longs

```python
COMMISSION_PER_CONTRACT = 0.65

if not has_liquidity:
    # Price each leg individually
    leg_contracts = []  # list of (contract, position, label)
    for p in opt_positions:
        c = p.contract
        if c.lastTradeDateOrContractMonth == target_expiry:
            leg_contracts.append((c, p.position, f'{c.strike}{c.right}'))

    leg_tickers = [ib.reqMktData(c) for c, _, _ in leg_contracts]
    ib.sleep(3)

    for (c, qty, label), t in zip(leg_contracts, leg_tickers):
        bid = t.bid if not util.isNan(t.bid) and t.bid != -1 else None
        ask = t.ask if not util.isNan(t.ask) and t.ask != -1 else None

        if qty < 0:
            # Short legs — always close (this is your risk)
            price = ask if ask else bid
            if price:
                action = 'BUY'
                order = LimitOrder(action, abs(qty), round_to_tick(price))
                trade = ib.placeOrder(c, order)
                print(f'  CLOSING short {label}: BUY {abs(qty)}x @ {round_to_tick(price)}')
            else:
                print(f'  WARNING: no price for short {label} — needs manual intervention')
        else:
            # Long legs — only close if value exceeds commission
            price = bid if bid else ask
            value_per_contract = price * 100 if price else 0
            if price and value_per_contract > COMMISSION_PER_CONTRACT:
                action = 'SELL'
                order = LimitOrder(action, abs(qty), round_to_tick(price))
                trade = ib.placeOrder(c, order)
                print(f'  CLOSING long {label}: SELL {abs(qty)}x @ {round_to_tick(price)} (value ${value_per_contract:.2f})')
            else:
                print(f'  SKIPPING long {label}: value ${value_per_contract:.2f} <= commission ${COMMISSION_PER_CONTRACT} — not worth closing')

    for t in leg_tickers:
        ib.cancelMktData(t.contract)
```

## Gotchas

- `avgCost` from `ib.portfolio()` is per-share (not per-contract). Multiply by position and 100 for total.
- For combo (BAG) entries, IBKR may report `avgCost` per-leg or per-combo depending on how the order filled. Verify against trade confirmations.
- Rolling a tested side often results in a net debit — you're buying back something expensive and selling something cheaper. Only roll if the debit is small relative to the remaining credit.
- Don't adjust more than once. Each adjustment adds legs, complicates the position, and increases transaction costs. If the first adjustment fails, close.
- Time-based exits protect against gamma risk. A 0DTE position at 3 PM can move from +50% to -100% in minutes.
