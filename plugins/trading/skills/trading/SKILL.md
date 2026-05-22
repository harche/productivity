---
name: trading
description: "Monitor your brokerage portfolio, check positions and balances, place trades, and analyze account performance on Interactive Brokers. Use when the user asks about their portfolio, wants market data, or needs to manage trades."
allowed-tools: Bash(curl:*),Bash(python3:*),Bash(${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# Trading (Interactive Brokers)

Manage your IBKR portfolio, get market data, and place trades via the Client Portal API.

## Before anything: ensure the gateway is running

```bash
curl -sk https://localhost:5000/v1/api/iserver/auth/status | python3 -m json.tool
# If not running/authenticated:
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/start_gateway.py --login
```

See [references/gateway.md](references/gateway.md) for login details, session management, and troubleshooting.

## Check portfolio and positions

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/account_summary.py          # account overview
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/monitor.py                   # all positions with live P/L
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/monitor.py --symbol SPX -g   # SPX positions with Greeks
```

Full API endpoints for accounts, positions, balances, and allocations -- see [references/portfolio.md](references/portfolio.md).

## Get market quotes

```bash
# Search for a contract, then get a snapshot (requires two calls -- first primes, second returns data)
curl -sk "https://localhost:5000/v1/api/trsrv/stocks?symbols=AAPL" | python3 -m json.tool
curl -sk "https://localhost:5000/v1/api/iserver/marketdata/snapshot?conids=265598&fields=31,84,86" | python3 -m json.tool
```

Contract search, historical data, scanners, and field IDs -- see [references/market-data.md](references/market-data.md).

## Place and manage orders

```bash
# Submit from a strategy file
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/submit_order.py order.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/submit_order.py order.json --dry-run   # preview first

# Cancel / modify
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancel_order.py <orderId>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/modify_order.py <orderId> --price -25.50
```

Order types, bracket orders, raw curl examples, and confirmation flow -- see [references/trading.md](references/trading.md).

## Build options strategies (iron butterfly AND iron condor)

**`iron_butterfly.py` handles BOTH iron butterflies and iron condors.** Use `--strategy N` to select a preset, or configure manually with `--short-offset`. When the user asks for an iron butterfly or iron condor without specifying parameters, suggest `--strategy 3` (iron condor with 60% profit target) as the default — it's marked "Best" in the strategies reference.

```bash
# Strategy 3: Iron condor, 60% profit target (recommended default)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/iron_butterfly.py today --strategy 3 --submit

# Strategy 1: Iron butterfly, hold to expiry
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/iron_butterfly.py today --strategy 1 --submit

# Strategy 4: Iron condor, hold to expiry
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/iron_butterfly.py today --strategy 4 --submit

# Preview without submitting (omit --submit)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/iron_butterfly.py today --strategy 3

# Close a position by strikes (no JSON file needed)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/close_position.py --strikes 7450P,7475P,7520C,7545C -y
```

See [references/strategies.md](references/strategies.md) for strategy presets (1-4), parameters, auto-close, close position, and bracket orders.

## View trade history and performance

```bash
curl -sk https://localhost:5000/v1/api/iserver/account/trades | python3 -m json.tool   # recent executions
curl -sk https://localhost:5000/v1/api/iserver/account/orders | python3 -m json.tool   # live orders
```

Performance analytics, transaction history, and allocation -- see [references/portfolio.md](references/portfolio.md).

## Rules

- **NEVER use market orders (MKT) for options, especially 0DTE. ALWAYS use limit orders (LMT).**
- **Always confirm with the user before placing, modifying, or cancelling orders.**
- **ALWAYS call `/iserver/accounts` FIRST before any market data or trading calls** -- this initializes the session.
- **Use `/iserver/marketdata/snapshot`** for market data (NOT `/md/snapshot`).
- Market data snapshots require two calls: first primes the subscription, wait 2-3s, then call again.
- Use `-k` on all curl calls (self-signed cert). Pipe through `python3 -m json.tool` for formatting.
- Call `curl -sk -X POST https://localhost:5000/v1/api/tickle` periodically to prevent session timeout.
- Rate limit: 10 requests/second. HTTP 429 = throttled.
