---
name: ibkr
description: Interact with Interactive Brokers (IBKR) Web API for trading, market data, portfolio management, and account information. Use when the user asks about stocks, options, orders, positions, portfolio, or anything related to their brokerage account.
allowed-tools: Bash(curl:*)
---

# IBKR Web API (Client Portal API)

Interact with Interactive Brokers using the official Client Portal Web API via `curl`.

## Prerequisites

The IBKR Client Portal Gateway must be running locally. This is a Java-based gateway that handles authentication and proxies API requests to IBKR servers.

### Starting the Gateway

```bash
# Download from: https://www.interactivebrokers.com/en/trading/ib-api.php
# Unzip and run:
cd ~/clientportal.gw && bin/run.sh root/conf.yaml

# Then open https://localhost:5000 in a browser to log in
```

After login, the gateway maintains a session that the API uses. No API key or token is needed — authentication is session-based via the gateway.

## Base URL

```
https://localhost:5000/v1/api
```

**Important:** The gateway uses a self-signed SSL certificate, so all `curl` calls must include `-k` (insecure) to skip certificate verification.

## Session Management

The gateway session times out after ~6 minutes of inactivity. Keep it alive by calling `/tickle` at least every 5 minutes.

```bash
# Check authentication status
curl -sk https://localhost:5000/v1/api/iserver/auth/status | python3 -m json.tool

# Keep session alive (call periodically)
curl -sk -X POST https://localhost:5000/v1/api/tickle | python3 -m json.tool

# Re-initialize brokerage session if timed out
curl -sk -X POST https://localhost:5000/v1/api/iserver/auth/ssodh/init | python3 -m json.tool

# Validate SSO session
curl -sk https://localhost:5000/v1/api/sso/validate | python3 -m json.tool

# Logout
curl -sk -X POST https://localhost:5000/v1/api/logout | python3 -m json.tool
```

**Session tip:** If `/iserver/auth/status` returns `connected:true` but `authenticated:false`, call `/iserver/auth/ssodh/init` to re-initialize. Always check auth status before making trading calls.

## Quick Start

```bash
# List accounts
curl -sk https://localhost:5000/v1/api/portfolio/accounts | python3 -m json.tool

# Get account summary
curl -sk https://localhost:5000/v1/api/portfolio/{accountId}/summary | python3 -m json.tool

# Get positions (page 0)
curl -sk https://localhost:5000/v1/api/portfolio/{accountId}/positions/0 | python3 -m json.tool

# Search for a stock contract (e.g., AAPL)
curl -sk https://localhost:5000/v1/api/trsrv/stocks?symbols=AAPL | python3 -m json.tool

# Get market data snapshot (conid 265598 = AAPL)
curl -sk "https://localhost:5000/v1/api/md/snapshot?conids=265598&fields=31,55,84,86" | python3 -m json.tool

# Get historical data
curl -sk -X POST https://localhost:5000/v1/api/hmds/history \
  -H "Content-Type: application/json" \
  -d '{"conid": 265598, "period": "1d", "bar": "1h"}' | python3 -m json.tool

# View live orders
curl -sk https://localhost:5000/v1/api/iserver/account/orders | python3 -m json.tool
```

## Rate Limits

- **Global limit:** 10 requests per second per authenticated username
- Exceeding the limit returns HTTP 429 (Too Many Requests)
- Violator IPs may be placed in a penalty box for 10 minutes

## References

Detailed command references:

* **Trading** — [references/trading.md](references/trading.md) — Orders, modifications, cancellations, order types
* **Market Data** — [references/market-data.md](references/market-data.md) — Snapshots, historical data, scanners
* **Portfolio** — [references/portfolio.md](references/portfolio.md) — Accounts, positions, balances, allocations, performance

## Important

- **Always confirm with the user before placing, modifying, or cancelling orders.**
- Always check session status before making trading calls.
- Use `-k` flag on all `curl` calls (self-signed cert).
- Use `python3 -m json.tool` to format JSON output.
- The `/portfolio/accounts` endpoint MUST be called before other `/portfolio` endpoints.
- For US Futures orders, the `manualIndicator` field is required.
- Only one active brokerage session can exist per username across all IBKR services.
- Call `/tickle` periodically to prevent session timeout.
