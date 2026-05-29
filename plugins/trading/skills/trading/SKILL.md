---
name: trading
description: "Monitor your brokerage portfolio, check positions and balances, place trades, and analyze account performance on Interactive Brokers. Use when the user asks about their portfolio, wants market data, or needs to manage trades. Also use for: historical price charts, stock/company lookup, market scanners (top gainers, most active, high dividend), and options pricing analysis."
allowed-tools: Bash(curl:*),Bash(python3:*),Bash(uv:*)
---

## How to use this skill

1. Read [references/INDEX.md](references/INDEX.md) to route to the relevant reference
2. Read the reference, then call the IB Client Portal REST API directly using `curl -sk` or inline Python with `requests`
3. Base URL: `https://localhost:5000/v1/api`

## Rules

- **NEVER use market orders (MKT) for options. ALWAYS use limit orders (LMT).**
- **Always confirm with the user before placing, modifying, or cancelling orders.**
- Client Portal Gateway must be running at `https://localhost:5000`.
- **MUST call `GET /iserver/accounts` before any market data or trading calls** — this initializes the iserver session.
- Market data snapshots require **two calls**: first primes the subscription, sleep 2.5s, second reads data.
- Use `curl -sk` (skip SSL verification — self-signed cert) or `requests.get(..., verify=False)`.
- Rate limit: 10 requests/second. HTTP 429 = throttled.
- Call `POST /tickle` every 4-5 minutes to prevent session timeout (~6 min inactivity).
