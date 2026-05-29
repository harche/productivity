# Connection & Session

Base URL: `https://localhost:5000/v1/api`

All calls use `-k` (curl) or `verify=False` (Python) — the gateway uses a self-signed cert.

## Check Authentication

```bash
curl -sk https://localhost:5000/v1/api/iserver/auth/status
```

Returns `{"authenticated": true, ...}` if session is active.

## Initialize Session

**MUST call before any market data or trading calls.** This initializes the iserver session.

```bash
curl -sk https://localhost:5000/v1/api/iserver/accounts
```

Without this, snapshot and order endpoints return empty or error responses.

## Keepalive

Session expires after ~6 minutes of inactivity. Ping periodically:

```bash
curl -sk -X POST https://localhost:5000/v1/api/tickle
```

If session has expired, re-initialize:

```bash
curl -sk -X POST https://localhost:5000/v1/api/iserver/auth/ssodh/init
```

If that doesn't work, re-authenticate at `https://localhost:5000` in the browser.

## Multi-Account Selection

```bash
curl -sk https://localhost:5000/v1/api/portfolio/accounts
```

Returns a list of account objects with `id`, `accountId`, `type`, `currency`. Present to user via AskUserQuestion — never assume an account.

## Rate Limit

10 requests/second per authenticated username. HTTP 429 = throttled — back off and retry after 1 second.

## Logout

```bash
curl -sk -X POST https://localhost:5000/v1/api/logout
```
