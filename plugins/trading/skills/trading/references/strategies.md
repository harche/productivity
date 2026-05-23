# Strategies: Iron Butterfly & Iron Condor

## Strategy Presets

Default recommendation: **Strategy 3** — best risk-adjusted returns.

| # | Name | Short Strikes | Exit |
|---|------|--------------|------|
| 1 | Iron Butterfly — Hold to Expiry | ATM | Hold |
| 2 | Iron Butterfly — 60% Profit Target | ATM | Buy back at 40% of credit |
| 3 | **Iron Condor — 60% Profit Target** | 0.3% OTM each side | Buy back at 40% of credit |
| 4 | Iron Condor — Hold to Expiry | 0.3% OTM each side | Hold |

## Constructing an Iron Butterfly / Condor

### Step 1: Get SPX price

```python
from ib_async import IB, Index, Option, Contract, ComboLeg, LimitOrder, util

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1, timeout=20)
spx = ib.qualifyContracts(Index('SPX', 'CBOE'))[0]
[ticker] = ib.reqTickers(spx)
ib.sleep(2)
spx_price = ticker.marketPrice()
```

### Step 2: Pick short strikes

**Iron Butterfly (ATM):** both shorts at nearest strike to SPX.

```python
STRIKE_INC = 5
atm = int(round(spx_price / STRIKE_INC) * STRIKE_INC)
short_put_strike = atm
short_call_strike = atm
```

**Iron Condor (OTM):** place shorts N% away from SPX.

```python
offset_pct = 0.003  # 0.3%
short_put_strike = int(round((spx_price * (1 - offset_pct)) / STRIKE_INC) * STRIKE_INC)
short_call_strike = int(round((spx_price * (1 + offset_pct)) / STRIKE_INC) * STRIKE_INC)
```

### Step 3: Find trading class and qualify shorts

```python
expiry = '20260527'  # YYYYMMDD

# Find trading class
chains = ib.reqSecDefOptParams('SPX', '', 'IND', spx.conId)
tc = 'SPXW'
for chain in chains:
    if chain.exchange == 'SMART' and expiry in chain.expirations:
        tc = chain.tradingClass
        break

# Also grab available strikes to validate later
avail_strikes = set()
for chain in chains:
    if chain.exchange == 'SMART' and chain.tradingClass == tc:
        avail_strikes = set(chain.strikes)
        break

# Qualify short legs
short_put = ib.qualifyContracts(Option('SPX', expiry, short_put_strike, 'P', 'SMART', tradingClass=tc))[0]
short_call = ib.qualifyContracts(Option('SPX', expiry, short_call_strike, 'C', 'SMART', tradingClass=tc))[0]
```

### Step 4: Price the shorts

```python
tickers = [ib.reqMktData(short_put), ib.reqMktData(short_call)]
ib.sleep(3)

def get_price(t):
    for val in [t.bid, t.ask, t.close]:
        if not util.isNan(val) and val != -1:
            return val
    return None

sp_price = get_price(tickers[0])
sc_price = get_price(tickers[1])
net_credit_shorts = sp_price + sc_price

for t in tickers:
    ib.cancelMktData(t.contract)
```

### Step 5: Calculate wing strikes

Wing width determines max loss. Target: `(ratio + 1) × net_credit`.

```python
ratio = 2.0  # max_loss = 2× max_profit
wing_width = int(round((ratio + 1.0) * net_credit_shorts / STRIKE_INC) * STRIKE_INC)
wing_width = max(wing_width, STRIKE_INC)

long_put_strike = short_put_strike - wing_width
long_call_strike = short_call_strike + wing_width
```

**Verify strikes exist** before qualifying:

```python
if long_put_strike not in avail_strikes:
    # Find nearest available strike
    long_put_strike = max(s for s in avail_strikes if s <= long_put_strike)
if long_call_strike not in avail_strikes:
    long_call_strike = min(s for s in avail_strikes if s >= long_call_strike)
```

### Step 6: Qualify wings and price them

```python
long_put = ib.qualifyContracts(Option('SPX', expiry, long_put_strike, 'P', 'SMART', tradingClass=tc))[0]
long_call = ib.qualifyContracts(Option('SPX', expiry, long_call_strike, 'C', 'SMART', tradingClass=tc))[0]

tickers = [ib.reqMktData(long_put), ib.reqMktData(long_call)]
ib.sleep(3)
lp_price = get_price(tickers[0])
lc_price = get_price(tickers[1])
for t in tickers:
    ib.cancelMktData(t.contract)
```

### Step 7: Calculate strategy metrics

```python
net_credit = net_credit_shorts - lp_price - lc_price
actual_wing = max(short_put_strike - long_put_strike, long_call_strike - short_call_strike)
max_profit = net_credit * 100
max_loss = (actual_wing - net_credit) * 100

print(f'Net Credit:  ${net_credit:.2f} (${max_profit:,.0f})')
print(f'Max Loss:    ${max_loss:,.0f}')
print(f'Wing Width:  {actual_wing} points')
print(f'Breakevens:  {short_put_strike - net_credit:.2f} / {short_call_strike + net_credit:.2f}')
```

### Step 8: Build combo and submit

See [orders.md](orders.md) for combo construction and submission.

Leg order: Long Put, Short Put, Short Call, Long Call.

Actions: BUY, SELL, SELL, BUY.

### 60% Profit Target Exit

After entry fills, place a standing LMT order to buy back at 40% of credit:

```python
close_price = round(net_credit * 0.40, 2)  # pay 40% to close
profit_order = LimitOrder('SELL', quantity, round_to_tick(-close_price))
```

## Gotchas

- Wing strikes may not exist for all expirations — always validate against `chain.strikes`
- Iterating wing width: wing ask prices reduce net credit, which reduces required wing width. May need 2-3 iterations to converge.
- SPX options settle to cash (European style) — no exercise risk before expiry.
- 0DTE options have extreme gamma — small moves cause large P/L swings.
