---
name: trading
description: "Monitor your brokerage portfolio, check positions and balances, place trades, and analyze account performance on Interactive Brokers. Use when the user asks about their portfolio, wants market data, or needs to manage trades."
allowed-tools: Bash(uv:*),Bash(python3:*)
---

## How to use this skill

1. Read [references/INDEX.md](references/INDEX.md) to route to the relevant reference
2. Read the reference, then write inline `ib_async` Python to accomplish the task
3. Run code with `cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 -c "..."`

## Rules

- **NEVER use market orders (MKT) for options. ALWAYS use limit orders (LMT).**
- **Always confirm with the user before placing, modifying, or cancelling orders.**
- IB Gateway must be running on port 4002 (paper) or 4001 (live).
