---
name: knowledge-base
description: Search and read Red Hat Knowledge Base articles, solutions, and documentation. Use when the user asks about known issues, troubleshooting, or wants to look up KB articles.
allowed-tools: Bash(curl:*)
---

# Red Hat Knowledge Base via Hydra Search API

Search and read Red Hat Knowledge Base articles, solutions, and documentation using the Hydra search API with `curl`.

## Authentication

Same two-step OAuth flow as support cases. Exchange the offline token for an access token:

```bash
# Get access token (run this first)
ACCESS_TOKEN=$(curl -s https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token \
  -d grant_type=refresh_token -d client_id=rhsm-api \
  -d "refresh_token=$(security find-generic-password -a "$USER" -s "RH_API_OFFLINE_TOKEN" -w)" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
```

The offline token is read directly from macOS Keychain — do NOT rely on `$RH_API_OFFLINE_TOKEN` being set in the environment, as the Bash tool does not source `~/.zshrc`.

## Base URL

```
https://access.redhat.com/hydra/rest/search/kcs
```

## Quick Start

```bash
# Get access token first
ACCESS_TOKEN=$(curl -s https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token \
  -d grant_type=refresh_token -d client_id=rhsm-api \
  -d "refresh_token=$(security find-generic-password -a "$USER" -s "RH_API_OFFLINE_TOKEN" -w)" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Search the knowledge base
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://access.redhat.com/hydra/rest/search/kcs?q=etcd+slow+fsync&rows=5" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Results: {data[\"response\"][\"numFound\"]}')
for doc in data['response']['docs']:
    print(f'  [{doc.get(\"documentKind\",\"\")}] {doc.get(\"publishedTitle\",\"\")[:70]}')
    print(f'    {doc.get(\"view_uri\",\"\")}')
"

# Search solutions only
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://access.redhat.com/hydra/rest/search/kcs?q=metallb+cordon&rows=5&fq=documentKind:Solution" \
  | python3 -m json.tool

# Fetch a specific article by ID
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://access.redhat.com/hydra/rest/search/kcs?q=*:*&rows=1&fq=id:7087003&fl=publishedTitle,abstract,view_uri,issue,solution_resolution,solution_rootcause,solution_environment,solution_diagnosticsteps" \
  | python3 -m json.tool

# Search by product
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://access.redhat.com/hydra/rest/search/kcs?q=upgrade+failure&rows=5&fq=documentKind:Solution&fq=boostProduct:openshift" \
  | python3 -m json.tool
```

## URL Parsing

When the user shares a KB URL like `https://access.redhat.com/solutions/7087003` or `https://access.redhat.com/articles/6873281`, extract the numeric ID from the path and fetch via:

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://access.redhat.com/hydra/rest/search/kcs?q=*:*&rows=1&fq=id:7087003&fl=publishedTitle,abstract,view_uri,issue,solution_resolution,solution_rootcause,solution_environment,solution_diagnosticsteps,product,lastModifiedDate,caseCount"
```

**Note:** The legacy `/rs/solutions/{id}` API is decommissioned. Always use the search endpoint with `fq=id:{articleId}` to fetch individual articles.

## References

Detailed search reference:

* **Search** — [references/search.md](references/search.md) — Query parameters, filters, field selection, pagination, common queries

## Important

- This is a **read-only** skill — no write operations are available.
- Always get a fresh access token before making API calls.
- Use `fq=documentKind:Solution` to limit results to solutions (most useful for troubleshooting).
- Use `fl=` to select specific fields and keep responses manageable.
- Solution articles include structured fields: `issue`, `solution_resolution`, `solution_rootcause`, `solution_environment`, `solution_diagnosticsteps`.
