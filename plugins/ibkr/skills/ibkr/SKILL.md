---
name: ibkr
description: Interact with Interactive Brokers (IBKR) Web API for trading, market data, portfolio management, and account information. Use when the user asks about stocks, options, orders, positions, portfolio, or anything related to their brokerage account.
allowed-tools: Bash(curl:*),Bash(~/ibkr/*)
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

**CRITICAL — Session Initialization:**
Before any market data or trading calls, you MUST call `/iserver/accounts` first. This initializes the iserver session. Without this call, market data snapshots will return conid-only responses with no price fields.

```bash
# STEP 1: ALWAYS call this first to initialize the iserver session
curl -sk https://localhost:5000/v1/api/iserver/accounts | python3 -m json.tool

# STEP 2: Now you can use market data and trading endpoints

# List portfolio accounts
curl -sk https://localhost:5000/v1/api/portfolio/accounts | python3 -m json.tool

# Get account summary
curl -sk https://localhost:5000/v1/api/portfolio/{accountId}/summary | python3 -m json.tool

# Get positions (page 0)
curl -sk https://localhost:5000/v1/api/portfolio/{accountId}/positions/0 | python3 -m json.tool

# Search for a stock contract (e.g., AAPL)
curl -sk https://localhost:5000/v1/api/trsrv/stocks?symbols=AAPL | python3 -m json.tool

# Get market data snapshot (conid 265598 = AAPL)
# NOTE: Use /iserver/marketdata/snapshot (NOT /md/snapshot) for reliable results.
# The first call primes the data (may return empty fields). Wait 2-3 seconds, then call again.
curl -sk "https://localhost:5000/v1/api/iserver/marketdata/snapshot?conids=265598&fields=31,55,84,86" | python3 -m json.tool

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
- **ALWAYS call `/iserver/accounts` FIRST before any market data or trading calls.** Without this, market data snapshots return empty field values. This is non-negotiable.
- **Use `/iserver/marketdata/snapshot` for market data** (NOT `/md/snapshot`). The `/md/snapshot` endpoint may not return field values reliably.
- **Market data snapshots require two calls**: the first call primes the data subscription (returns conid only, no fields). Wait 2-3 seconds, then call again to get actual prices.
- Always check session status before making trading calls.
- Use `-k` flag on all `curl` calls (self-signed cert).
- Use `python3 -m json.tool` to format JSON output.
- The `/portfolio/accounts` endpoint MUST be called before other `/portfolio` endpoints.
- For US Futures orders, the `manualIndicator` field is required.
- Only one active brokerage session can exist per username across all IBKR services.
- Call `/tickle` periodically to prevent session timeout.

## Automation Scripts

Scripts live in `~/ibkr/` and use a venv at `~/ibkr/.venv/`. Run with `~/ibkr/.venv/bin/python3` or the shebang.

### 1. Iron Butterfly Builder: `iron_butterfly.py`

Builds an SPX iron butterfly order (max_loss = 2x max_profit) and saves it as a JSON file.

```bash
~/ibkr/iron_butterfly.py <expiry> [--quantity N] [--output FILE] [--submit]
```

- `expiry`: "today", "tomorrow", or YYYY-MM-DD
- **IMPORTANT**: When the user asks for an iron butterfly with a relative date like "1 day expiry" or "tomorrow", first determine the actual calendar date, then pass it to the script. If today is a Friday, "tomorrow" would be Saturday (no market) — confirm with the user.
- `--submit`: immediately pipes the output to `submit_order.py`
- Output: JSON file (default: `iron_butterfly_<date>.json`)

```bash
# Build order for tomorrow
~/ibkr/iron_butterfly.py tomorrow

# Build and immediately submit
~/ibkr/iron_butterfly.py 2026-03-10 --quantity 2 --submit
```

### 2. Order Submitter: `submit_order.py`

Generic order submitter — works with **any ticker, any price, individual or combo orders**.

```bash
# From JSON file (output of iron_butterfly.py or any strategy builder)
~/ibkr/submit_order.py iron_butterfly_2026-03-06.json

# Dry run — show order details without submitting
~/ibkr/submit_order.py iron_butterfly_2026-03-06.json --dry-run

# Skip confirmation prompt
~/ibkr/submit_order.py iron_butterfly_2026-03-06.json -y

# Inline single contract order
~/ibkr/submit_order.py --account DUXXXXXXX --conid 265598 --side BUY \
    --quantity 10 --order-type LMT --price 150.00 --tif DAY

# Inline combo order
~/ibkr/submit_order.py --account DUXXXXXXX \
    --conidex "416904;;;854745265/1,849314253/-1" \
    --side BUY --quantity 1 --order-type LMT --price -35.00 --tif DAY
```

### JSON Order Format

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
