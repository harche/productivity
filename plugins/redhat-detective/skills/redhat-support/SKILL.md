---
name: redhat-support
description: Interact with Red Hat Jira (redhat.atlassian.net), search Red Hat Knowledge Base articles and solutions, and manage Customer Portal support cases. Use when the user asks about Jira issues, shares a Jira URL, asks about known issues, troubleshooting, knowledge base articles, support cases, shares a case/knowledge base URL, mentions issue keys like OCPBUGS-*, OCPNODE-*, any redhat.atlassian.net link, or asks about Node team work — bugs, epics, sprints, triage, standup prep, release readiness, escalations, CVEs, customer issues, CRI-O, kubelet, kueue, DRA, device manager, or any OpenShift Node component.
allowed-tools: Bash(acli:*,curl:*)
---

# Red Hat Support

Jira uses the Atlassian CLI (`acli`). Knowledge Base and Support Cases use `curl` with OAuth.

Use `acli jira -h` and `acli jira workitem -h` to discover commands and flags.

## Quick Start

### Jira

```bash
acli jira workitem view OCPNODE-4151
acli jira workitem view OCPNODE-4151 --fields '*all' --json
acli jira workitem search --jql 'assignee = currentUser() AND type = Epic AND status not in (Closed, Done)' --limit 10
acli jira workitem search --jql '"Epic Link" = OCPNODE-4151' --fields "key,summary,status,assignee"
```

### Knowledge Base

```bash
# macOS
RH_OFFLINE_TOKEN=$(security find-generic-password -a "$USER" -s "RH_API_OFFLINE_TOKEN" -w)
# Linux
RH_OFFLINE_TOKEN=$(secret-tool lookup service redhat key RH_API_OFFLINE_TOKEN)

ACCESS_TOKEN=$(curl -s https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token \
  -d grant_type=refresh_token -d client_id=rhsm-api \
  -d "refresh_token=$RH_OFFLINE_TOKEN" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://access.redhat.com/hydra/rest/search/kcs?q=etcd+slow+fsync&rows=5" | python3 -m json.tool
```

### Support Cases

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://api.access.redhat.com/support/v1/cases/04378910" | python3 -m json.tool
```

## URL Parsing

- **Jira**: `https://redhat.atlassian.net/browse/OCPNODE-4151` — extract the issue key after `/browse/`
- **Knowledge Base**: `https://access.redhat.com/solutions/7087003` — extract numeric ID, fetch via `fq=id:{articleId}`
- **Cases**: `https://access.redhat.com/support/cases/#/case/04378910` — extract case number after `/case/`

## References

Read based on what the user needs:

| User intent | Read |
|---|---|
| Node team work (bugs, epics, sprints, standup, triage, investigation, release) | [node-guide.md](references/node-guide.md) — it routes to the right reference |
| Jira command syntax (`acli` usage) | [jira.md](references/jira.md) |
| Knowledge Base search | [knowledge-base.md](references/knowledge-base.md) |
| Support cases | [cases.md](references/cases.md) |

For Node team queries, **always start with node-guide.md** — it provides the domain context and points to the specific reference for each workflow.

## Important

- **Always include clickable Jira URLs**: `https://redhat.atlassian.net/browse/{KEY}`
- **Always confirm with the user before any write operation** (create, edit, comment, transition).
- Always get a fresh OAuth access token before KB or case API calls.
- Epic children: JQL `"Epic Link" = EPIC-KEY` (not `parentEpic`).
- KB is read-only. Jira and cases support read and write.
