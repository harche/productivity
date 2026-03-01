---
name: support-cases
description: View, search, and manage Red Hat Customer Portal support cases. Use when the user asks about support cases, shares a case URL, or wants to look up cases referenced in Jira bugs.
allowed-tools: Bash(curl:*)
---

# Red Hat Support Cases via REST API

Interact with Red Hat Customer Portal support cases using the Hydra REST API with `curl`.

## Authentication

Requests require a two-step OAuth flow. First exchange the offline token for an access token, then use it:

```bash
# Step 1: Get access token (short-lived)
ACCESS_TOKEN=$(curl -s https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token \
  -d grant_type=refresh_token -d client_id=rhsm-api \
  -d "refresh_token=$RH_API_OFFLINE_TOKEN" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Step 2: Use in API calls
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "<url>" | python3 -m json.tool
```

**Important:** Always get a fresh access token at the start of each request sequence. Access tokens expire quickly. The offline token (`$RH_API_OFFLINE_TOKEN`) is sourced from `~/.zshrc`.

## Base URL

```
https://api.access.redhat.com/support/v1
```

## Quick Start

```bash
# Get access token (run this first, then use $ACCESS_TOKEN in subsequent calls)
ACCESS_TOKEN=$(curl -s https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token \
  -d grant_type=refresh_token -d client_id=rhsm-api \
  -d "refresh_token=$RH_API_OFFLINE_TOKEN" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# View a specific case
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://api.access.redhat.com/support/v1/cases/04378910" \
  | python3 -m json.tool

# List recent cases (your accessible cases)
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{"maxResults": 10}' \
  | python3 -m json.tool

# Search cases by keyword
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{"maxResults": 10, "keyword": "metallb"}' \
  | python3 -m json.tool

# Get comments on a case
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://api.access.redhat.com/support/v1/cases/04378910/comments" \
  | python3 -m json.tool
```

## URL Parsing

When the user shares a support case URL like `https://access.redhat.com/support/cases/#/case/04378910`, extract the case number (`04378910`) from the path after `/case/` and use it in API calls.

Case numbers are typically 8-digit strings (e.g., `04378910`). They also appear in Jira bug SFDC case link fields.

## References

Detailed command references:

* **Cases** — [references/cases.md](references/cases.md) — View, comment, attachments, case fields
* **Search** — [references/search.md](references/search.md) — Filter parameters, pagination, common queries

## Important

- **Always confirm with the user before adding comments, updating cases, or any write operation.**
- Always get a fresh access token before making API calls — tokens expire quickly.
- Case responses include comments by default. Use `python3` to extract specific fields.
- The API returns cases accessible to the authenticated user's account.
- All actions happen as the token owner.
