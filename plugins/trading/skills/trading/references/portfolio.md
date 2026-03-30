# Portfolio and Account Reference

API endpoints for accounts, positions, balances, allocations, performance, and transaction history.

> **Note:** The `/portfolio/accounts` endpoint MUST be called before other `/portfolio` endpoints.

## Accounts

```bash
# List all portfolio accounts (MUST call first)
curl -sk https://localhost:5000/v1/api/portfolio/accounts | python3 -m json.tool

# Get sub-accounts (for tiered account structures, up to 100)
curl -sk https://localhost:5000/v1/api/portfolio/subaccounts | python3 -m json.tool

# Paginated sub-accounts (20 per page)
curl -sk "https://localhost:5000/v1/api/portfolio/subaccounts2?page=0" | python3 -m json.tool

# Account metadata
curl -sk https://localhost:5000/v1/api/portfolio/{accountId}/meta | python3 -m json.tool

# Tradeable accounts (iserver)
curl -sk https://localhost:5000/v1/api/iserver/accounts | python3 -m json.tool
```

## Account Summary

```bash
curl -sk https://localhost:5000/v1/api/portfolio/{accountId}/summary | python3 -m json.tool
```

Key summary fields:
- `netliquidation` -- Net liquidation value
- `totalcashvalue` -- Total cash
- `grosspositionvalue` -- Gross position value
- `buyingpower` -- Available buying power
- `maintmarginreq` -- Maintenance margin requirement
- `availablefunds` -- Available funds
- `excessliquidity` -- Excess liquidity
- `unrealizedpnl` -- Unrealized P&L
- `realizedpnl` -- Realized P&L

## Positions

```bash
# Get positions (paginated, 30 per page, start at page 0)
curl -sk https://localhost:5000/v1/api/portfolio/{accountId}/positions/0 | python3 -m json.tool

# Page 1
curl -sk https://localhost:5000/v1/api/portfolio/{accountId}/positions/1 | python3 -m json.tool

# Get a specific position by contract ID
curl -sk https://localhost:5000/v1/api/portfolio/{accountId}/position/{conid} | python3 -m json.tool

# Invalidate position cache (force refresh)
curl -sk -X POST https://localhost:5000/v1/api/portfolio/{accountId}/positions/invalidate | python3 -m json.tool
```

Position response fields:
- `conid` -- Contract ID
- `contractDesc` -- Contract description
- `position` -- Number of shares/contracts
- `mktPrice` -- Current market price
- `mktValue` -- Market value of position
- `avgCost` -- Average cost basis
- `avgPrice` -- Average entry price
- `unrealizedPnl` -- Unrealized P&L
- `realizedPnl` -- Realized P&L

## Asset Allocation

```bash
# Allocation by asset class, sector, industry for single account
curl -sk https://localhost:5000/v1/api/portfolio/{accountId}/allocation | python3 -m json.tool

# Consolidated allocation across multiple accounts
curl -sk -X POST https://localhost:5000/v1/api/portfolio/allocation \
  -H "Content-Type: application/json" \
  -d '{"acctIds": ["U1234567", "U7654321"]}' | python3 -m json.tool
```

## Performance (Portfolio Analyst)

```bash
# Daily performance
curl -sk -X POST https://localhost:5000/v1/api/pa/performance \
  -H "Content-Type: application/json" \
  -d '{"acctIds": ["{accountId}"], "freq": "D"}' | python3 -m json.tool

# Monthly performance
curl -sk -X POST https://localhost:5000/v1/api/pa/performance \
  -H "Content-Type: application/json" \
  -d '{"acctIds": ["{accountId}"], "freq": "M"}' | python3 -m json.tool
```

Frequency options: `D` (daily), `M` (monthly), `Q` (quarterly)

## Transaction History

```bash
# Get transactions for a specific contract
curl -sk -X POST https://localhost:5000/v1/api/pa/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "acctIds": ["{accountId}"],
    "conids": [265598],
    "days": 30
  }' | python3 -m json.tool

# With specific currency
curl -sk -X POST https://localhost:5000/v1/api/pa/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "acctIds": ["{accountId}"],
    "conids": [265598],
    "currency": "USD",
    "days": 90
  }' | python3 -m json.tool
```

## Notifications (FYI)

```bash
# Get unread notification count
curl -sk https://localhost:5000/v1/api/fyi/unreadnumber | python3 -m json.tool

# List notifications
curl -sk "https://localhost:5000/v1/api/fyi/notifications?max=10" | python3 -m json.tool

# Mark notification as read
curl -sk -X PUT https://localhost:5000/v1/api/fyi/notifications/{notificationId} | python3 -m json.tool
```
