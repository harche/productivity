# Portfolio Greeks & Risk

## Aggregate Portfolio Greeks

Fetch option positions, then get Greeks via snapshot fields.

```python
import requests, time, urllib3
urllib3.disable_warnings()

BASE = "https://localhost:5000/v1/api"

# Get option positions
positions = []
page = 0
while True:
    data = requests.get(f"{BASE}/portfolio/{account_id}/positions/{page}", verify=False).json()
    if not data:
        break
    positions.extend(data)
    if len(data) < 30:
        break
    page += 1

opt_positions = [p for p in positions if p.get("assetClass") == "OPT"]

if not opt_positions:
    print("No option positions found.")
else:
    conids = ",".join(str(p["conid"]) for p in opt_positions)
    
    # Get Greeks
    requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={conids}&fields=7308,7309,7310,7311,7633", verify=False)
    time.sleep(3)
    greeks_data = requests.get(f"{BASE}/iserver/marketdata/snapshot?conids={conids}&fields=7308,7309,7310,7311,7633", verify=False).json()
    
    def parse(val):
        if val is None: return None
        try: return float(str(val).lstrip("CHT"))
        except: return None
    
    greeks_by_conid = {}
    for item in greeks_data:
        greeks_by_conid[item["conid"]] = {
            "delta": parse(item.get("7308")),
            "gamma": parse(item.get("7309")),
            "theta": parse(item.get("7310")),
            "vega": parse(item.get("7311")),
            "iv": item.get("7633"),
        }
    
    net_delta = net_gamma = net_theta = net_vega = 0.0
    for p in opt_positions:
        g = greeks_by_conid.get(p["conid"], {})
        qty = p["position"]
        if g.get("delta") is not None:
            net_delta += g["delta"] * qty
            net_gamma += g["gamma"] * qty
            net_theta += g["theta"] * qty
            net_vega += g["vega"] * qty
            print(f'  {p["contractDesc"]:>30}  qty={qty:+.0f}  d={g["delta"]:+.4f}  g={g["gamma"]:.4f}  t={g["theta"]:.4f}  v={g["vega"]:.4f}')
```

## Dollar-Weighted Exposure

```python
multiplier = 100  # SPX options multiplier
delta_dollars = net_delta * spx_price * multiplier
daily_theta = net_theta * multiplier
vega_dollars = net_vega * multiplier

print(f"  Net Delta:  {net_delta:+.4f}  (${delta_dollars:+,.0f} per 1-pt SPX move)")
print(f"  Net Theta:  {net_theta:+.4f}  (${daily_theta:+,.0f}/day)")
print(f"  Net Vega:   {net_vega:+.4f}  (${vega_dollars:+,.0f} per 1% IV change)")
```

## Correlation Warning

Multiple SPX positions across expirations are correlated bets, not diversification. A large SPX move hits ALL of them simultaneously. Always sum total exposure across all expirations.

## Gotchas

- Greeks are point-in-time snapshots — they change with every tick. Run during market hours for accuracy.
- Gamma risk grows exponentially as expiry approaches — a flat delta with high gamma can blow up fast.
- Portfolio theta is your "daily paycheck" only if SPX stays flat. Real P/L depends on gamma exposure too.
- Greek values from snapshots may have string prefixes — always parse.
