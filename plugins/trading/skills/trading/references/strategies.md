# Options Strategies and Automation Scripts

Scripts for building, submitting, and managing options positions. All scripts are in `${CLAUDE_PLUGIN_ROOT}/scripts/` and import from the shared `ibkr_client.py` module.

## Iron Butterfly Builder: `iron_butterfly.py`

Builds an SPX iron butterfly order and saves it as a JSON file.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/iron_butterfly.py <expiry> [--quantity N] [--ratio R] [--output FILE] [--submit] [--bracket PROFIT STOP_LOSS]
```

- `expiry`: "today", "tomorrow", or YYYY-MM-DD
- **IMPORTANT**: When the user asks for a relative date like "1 day expiry" or "tomorrow", determine the actual calendar date first. If today is Friday, "tomorrow" is Saturday (no market) -- confirm with the user.
- `--ratio`: Target max_loss/max_profit ratio (default: 2.0). Lower = tighter wings, less capital.
- `--submit`: Immediately submits the order via `submit_order.py`
- `--bracket PROFIT STOP_LOSS`: Attach bracket orders (profit target + stop-loss in dollars). Requires `--submit`. Submits entry first, waits for fill, then submits OCA-linked profit target (LMT) and stop-loss (STP LMT) on the combo.
- Output: JSON file (default: `iron_butterfly_<date>.json`)
- Retries on transient 5xx API errors (up to 2 retries)

```bash
# Build order for tomorrow
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/iron_butterfly.py tomorrow

# Build with custom risk/reward ratio
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/iron_butterfly.py today --ratio 2.0

# Build and immediately submit
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/iron_butterfly.py 2026-03-10 --quantity 2 --submit

# Build with bracket: $2000 profit target, $4000 stop-loss
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/iron_butterfly.py today --bracket 2000 4000 --submit
```

## Order Submitter: `submit_order.py`

Generic order submitter -- works with any ticker, any price, individual or combo orders.

```bash
# From JSON file (output of iron_butterfly.py or any strategy builder)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/submit_order.py iron_butterfly_2026-03-06.json

# Dry run -- show order details AND live price comparison
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/submit_order.py iron_butterfly_2026-03-06.json --dry-run

# Skip confirmation prompt
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/submit_order.py iron_butterfly_2026-03-06.json -y

# Inline single contract order
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/submit_order.py --account DUXXXXXXX --conid 265598 --side BUY \
    --quantity 10 --order-type LMT --price 150.00 --tif DAY

# Inline combo order
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/submit_order.py --account DUXXXXXXX \
    --conidex "416904;;;854745265/1,849314253/-1" \
    --side BUY --quantity 1 --order-type LMT --price -35.00 --tif DAY
```

- Retries on transient 5xx API errors (up to 2 retries)
- Dry run shows live prices alongside saved prices so you can see if the market has moved

## Close Position: `close_position.py`

Closes a combo position and cancels related standing orders (profit target, stop-loss).

```bash
# Close position from order file (fetches live prices, calculates close price)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/close_position.py iron_butterfly_2026-03-12.json

# With larger buffer for faster fill
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/close_position.py iron_butterfly_2026-03-12.json --buffer 1.0

# Skip confirmation
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/close_position.py iron_butterfly_2026-03-12.json -y
```

- Reads leg data from the JSON file to calculate close cost
- Fetches live bid/ask for each leg
- Uses ask for legs being bought back, bid for legs being sold
- Adds configurable buffer (default: $0.50) for fill certainty
- Submits reverse combo limit order
- Automatically cancels any standing orders on the same combo

## Auto-Close: `auto_close.py`

Submits standing limit orders to close a combo position at a profit target or stop-loss. IBKR executes automatically when the price hits -- no polling needed.

```bash
# Close at $300 profit
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_close.py iron_butterfly_2026-03-11.json --profit 300

# Close at $500 max loss
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_close.py iron_butterfly_2026-03-11.json --stop-loss 500

# Both profit target and stop-loss
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_close.py iron_butterfly_2026-03-11.json --profit 300 --stop-loss 500
```

- Takes the same JSON file output by `iron_butterfly.py` (needs `metadata.net_credit`)
- **Profit target:** standing LMT order at `net_credit - (target$ / 100 / qty)`
- **Stop-loss:** STP order -- becomes market order when `net_credit + (loss$ / 100 / qty)` is hit

## Cancel Orders: `cancel_order.py`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancel_order.py 3212818              # cancel single
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancel_order.py 3212818 3212819      # cancel multiple
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancel_order.py --all                # cancel all open
```

## Modify Orders: `modify_order.py`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/modify_order.py 3212818 --price -25.50
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/modify_order.py 3212818 --quantity 2
```

- Shows current order details before and after modification
- Carries forward required fields (conid, orderType, side, tif)

## Position Monitor: `monitor.py`

```bash
# Show all positions (one-shot)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/monitor.py

# Filter by symbol
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/monitor.py --symbol SPX

# Auto-refresh every 30 seconds
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/monitor.py --watch 30

# Watch SPX positions every 15 seconds
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/monitor.py -s SPX -w 15

# Show Greeks (delta, theta, IV) for option positions
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/monitor.py --greeks
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/monitor.py -s SPX -g
```

- Groups positions by asset class (OPTIONS, STOCKS, etc.)
- Shows position size, market price, market value, unrealized P/L, and % P/L
- `--greeks` / `-g` adds delta, theta, and implied volatility columns for options
- `--watch` mode clears screen and refreshes on interval

## Account Summary: `account_summary.py`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/account_summary.py
```

Displays: Net Liquidation Value, Equity, Available Funds, Buying Power, Maintenance/Initial Margin, Cushion, Day Trades Remaining.

## JSON Order Format

Strategy builders output JSON in this format, consumed by `submit_order.py`:

```json
{
    "account_id": "DUXXXXXXX",
    "orders": [
        {
            "conidex": "416904;;;conid1/1,conid2/-1,...",
            "orderType": "LMT",
            "side": "BUY",
            "price": -72.20,
            "quantity": 1,
            "tif": "DAY"
        }
    ],
    "metadata": { "strategy": "iron_butterfly", ... }
}
```
