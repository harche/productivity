# Gateway and Session Management

The IBKR Client Portal Gateway must be running locally for all API access. It handles authentication and proxies requests to IBKR servers.

## Starting the Gateway

```bash
# Start and auto-login (paper account, default)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/start_gateway.py --login

# Start and auto-login (live account)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/start_gateway.py --login live

# Start without login
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/start_gateway.py

# Custom gateway path
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/start_gateway.py --path /custom/path
```

The script searches common locations (`~/ibkr`, `~/clientportal.gw`, `~/clientportal`, `~/ib_gateway`, `~/IBKR`), starts the gateway, and waits up to 60s for port 5000.

## Login

```bash
# Paper account (default)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/login_gateway.py

# Live account
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/login_gateway.py --account live
```

- Credentials are stored in macOS Keychain: `ibkr-{paper,live}-username`, `ibkr-{paper,live}-password`
- Uses `playwright-cli` (headless browser) for automated login
- Handles Live/Paper account toggle automatically
- If 2FA is required (live accounts), submits credentials and prompts to approve via IB Key app
- Skips if already authenticated

## Base URL

```
https://localhost:5000/v1/api
```

All `curl` calls must include `-k` (self-signed SSL certificate).

## Session Management

The gateway session times out after ~6 minutes of inactivity.

```bash
# Check authentication status
curl -sk https://localhost:5000/v1/api/iserver/auth/status | python3 -m json.tool

# Keep session alive (call at least every 5 minutes)
curl -sk -X POST https://localhost:5000/v1/api/tickle | python3 -m json.tool

# Re-initialize brokerage session if timed out
curl -sk -X POST https://localhost:5000/v1/api/iserver/auth/ssodh/init | python3 -m json.tool

# Validate SSO session
curl -sk https://localhost:5000/v1/api/sso/validate | python3 -m json.tool

# Logout
curl -sk -X POST https://localhost:5000/v1/api/logout | python3 -m json.tool
```

**Troubleshooting:** If `/iserver/auth/status` returns `connected:true` but `authenticated:false`, call `/iserver/auth/ssodh/init` to re-initialize. Always check auth status before making trading calls.

## Session Initialization (Critical)

Before any market data or trading calls, you MUST call `/iserver/accounts` first. This initializes the iserver session. Without this, market data snapshots return conid-only responses with no price fields.

```bash
curl -sk https://localhost:5000/v1/api/iserver/accounts | python3 -m json.tool
```

Similarly, `/portfolio/accounts` MUST be called before other `/portfolio` endpoints.

## Rate Limits

- **Global limit:** 10 requests per second per authenticated username
- Exceeding the limit returns HTTP 429 (Too Many Requests)
- Violator IPs may be placed in a penalty box for 10 minutes

## Important Notes

- Only one active brokerage session can exist per username across all IBKR services
- No API key or token is needed -- authentication is session-based via the gateway
- Call `/tickle` periodically to prevent session timeout
