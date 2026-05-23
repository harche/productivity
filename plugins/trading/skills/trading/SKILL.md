---
name: trading
description: "Monitor your brokerage portfolio, check positions and balances, place trades, and analyze account performance on Interactive Brokers. Use when the user asks about their portfolio, wants market data, or needs to manage trades."
allowed-tools: Bash(uv:*),Bash(python3:*),Bash(${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# Trading (Interactive Brokers)

Manage your IBKR portfolio, get market data, and place trades via IB Gateway + ib_async.

## Before anything: ensure IB Gateway is running

IB Gateway must be running and authenticated on port 4002 (paper) or 4001 (live).
All scripts use `ib_async` via the TWS socket API — no REST/curl calls needed.

```bash
# Quick connectivity test
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 -c "
from scripts.ib_client import connect, get_spx_price
ib = connect()
print(f'SPX: {get_spx_price(ib)}')
ib.disconnect()
"
```

## Check portfolio and positions

```bash
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/account_summary.py          # account overview
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/monitor.py                   # all positions with live P/L
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/monitor.py --symbol SPX -g   # SPX positions with Greeks
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/monitor.py --watch 30        # refresh every 30s
```

## Place and manage orders

```bash
# Submit from a strategy file
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/submit_order.py order.json
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/submit_order.py order.json --dry-run

# Submit inline
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/submit_order.py --symbol AAPL --side BUY --quantity 10 --price 150.00

# Cancel all open orders
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/cancel_order.py --all

# Modify price on an open order
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/modify_order.py --price -25.50
```

## Build options strategies (iron butterfly AND iron condor)

**`iron_butterfly.py` handles BOTH iron butterflies and iron condors.** Use `--strategy N` to select a preset, or configure manually with `--short-offset`. When the user asks for an iron butterfly or iron condor without specifying parameters, suggest `--strategy 3` (iron condor with 60% profit target) as the default.

```bash
# Strategy 3: Iron condor, 60% profit target (recommended default)
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/iron_butterfly.py today --strategy 3 --submit

# Strategy 1: Iron butterfly, hold to expiry
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/iron_butterfly.py today --strategy 1 --submit

# Strategy 4: Iron condor, hold to expiry
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/iron_butterfly.py today --strategy 4 --submit

# Preview without submitting (omit --submit)
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/iron_butterfly.py today --strategy 3

# Bracket orders (entry + profit target + stop-loss)
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/iron_butterfly.py today --strategy 3 --bracket 2000 4000 --submit

# Close a position by strikes
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/close_position.py --strikes 7450P,7475P,7520C,7545C -y

# Auto-close with profit target and/or stop-loss
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/auto_close.py iron_condor_2026-05-23.json --profit 300 --stop-loss 500
```

## Box spreads (lending / borrowing)

```bash
# Preview a 3-month box spread (lending $10k)
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/box_spread.py --amount 10000 --months 3

# Execute with custom rate
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/box_spread.py --amount 10000 --months 3 --rate 4.5 --execute

# Short box (borrowing)
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/box_spread.py --s1 5800 --s2 5900 --months 4 --short --execute

# Manual strikes
cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 scripts/box_spread.py --s1 7400 --s2 7500 --months 3 --execute
```

## Rules

- **NEVER use market orders (MKT) for options, especially 0DTE. ALWAYS use limit orders (LMT).**
- **Always confirm with the user before placing, modifying, or cancelling orders.**
- All scripts use `uv run` from `${CLAUDE_PLUGIN_ROOT}` to use the project's virtual environment.
- IB Gateway port: 4002 (paper), 4001 (live). All scripts default to 4002.
- All scripts use clientId=1 to avoid leaking stale client sessions.
- ib_async handles keepalive automatically — no tickle calls needed.
