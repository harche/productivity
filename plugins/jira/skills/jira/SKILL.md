---
name: jira
description: Interact with Jira (issues.redhat.com) to view, search, create, and update issues, epics, bugs, and more. Use when the user asks about Jira issues, shares a Jira URL, or wants to manage work items.
allowed-tools: Bash(curl:*)
---

# Jira via REST API

Interact with Red Hat Jira (issues.redhat.com) using the REST API v2 with `curl`.

## Authentication

All requests use a Bearer token from `$JIRA_API_TOKEN` (sourced from `~/.zshrc`):

```bash
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" "<url>" | python3 -m json.tool
```

**PAT limitation**: `currentUser()` in JQL and the `/rest/api/2/myself` endpoint do NOT work with PATs on Red Hat Jira. To find the token owner's username, use the session endpoint:

```bash
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/auth/1/session" | python3 -m json.tool
```

Then use the `name` field (e.g., `harpatil@redhat.com`) in JQL queries like `assignee="harpatil@redhat.com"`.

## Base URL

```
https://issues.redhat.com/rest/api/2
```

## Quick Start

```bash
# View an issue (from URL like https://issues.redhat.com/browse/OCPNODE-4151)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/OCPNODE-4151?fields=summary,status,assignee,priority,issuetype,description,created,updated,components,labels,fixVersions" \
  | python3 -m json.tool

# Search issues with JQL (use explicit email, NOT currentUser())
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/search?jql=assignee%3D%22harpatil%40redhat.com%22+AND+type%3DEpic+AND+status+not+in+(Closed,Done)&maxResults=10&fields=summary,status,assignee,priority" \
  | python3 -m json.tool

# Get children of an epic
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/search?jql=%22Epic+Link%22%3DOCPNODE-4151&fields=summary,status,assignee,issuetype,priority" \
  | python3 -m json.tool

# Get comments on an issue
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/OCPBUGS-77349/comment" \
  | python3 -m json.tool

# Add a comment (ALWAYS confirm with user first)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://issues.redhat.com/rest/api/2/issue/OCPBUGS-77349/comment" \
  -d '{"body": "Comment text here"}' \
  | python3 -m json.tool
```

## URL Parsing

When the user shares a Jira URL like `https://issues.redhat.com/browse/OCPNODE-4151`, extract the issue key (`OCPNODE-4151`) from the path after `/browse/` and use it in API calls.

## References

Detailed command references:

* **Issues** — [references/issues.md](references/issues.md) — View, create, update, comment, transition
* **Search** — [references/search.md](references/search.md) — JQL syntax, field filters, pagination, common queries

## Important

- **Always confirm with the user before creating issues, adding comments, transitioning status, or any write operation.**
- Use `fields=` parameter to limit response size — full issue responses are very large.
- Use `python3 -m json.tool` to format JSON output for readability.
- Epic children are found via JQL `"Epic Link"=EPIC-KEY`, NOT `parentEpic`.
- All actions happen as the token owner.
