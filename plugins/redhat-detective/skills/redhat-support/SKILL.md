---
name: redhat-support
description: Interact with Red Hat Jira (redhat.atlassian.net), search Red Hat Knowledge Base articles and solutions, and manage Customer Portal support cases. Use when the user asks about Jira issues, shares a Jira URL, asks about known issues, troubleshooting, knowledge base articles, support cases, shares a case/knowledge base URL, mentions issue keys like OCPBUGS-*, OCPNODE-*, any redhat.atlassian.net link, or asks about Node team work — bugs, epics, sprints, triage, standup prep, release readiness, escalations, CVEs, customer issues, CRI-O, kubelet, kueue, DRA, device manager, or any OpenShift Node component.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/*),Bash(curl:*)
---

# Red Hat Support

Jira uses the bundled `jira.sh` CLI (REST API via curl). Knowledge Base and Support Cases use `curl` with OAuth.

## Quick Start

### Jira

```bash
# View an issue
${CLAUDE_PLUGIN_ROOT}/scripts/jira.sh get OCPNODE-4151

# Search issues
${CLAUDE_PLUGIN_ROOT}/scripts/jira.sh search 'assignee = currentUser() AND type = Epic AND status not in (Closed, Done)' 10

# Deep dive (full issue + comments + linked issues)
${CLAUDE_PLUGIN_ROOT}/scripts/jira.sh issue-deep-dive OCPNODE-4151

# Add a remote link (e.g., GitHub PR)
${CLAUDE_PLUGIN_ROOT}/scripts/jira.sh link OCPNODE-4151 "https://github.com/org/repo/pull/123" "PR title"
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
| Jira command syntax (`jira.sh` usage) | [jira.md](references/jira.md) |
| Knowledge Base search | [knowledge-base.md](references/knowledge-base.md) |
| Support cases | [cases.md](references/cases.md) |

For Node team queries, **always start with node-guide.md** — it provides the domain context and points to the specific reference for each workflow.

## Important

- **Always include clickable Jira URLs**: `https://redhat.atlassian.net/browse/{KEY}`
- **Always confirm with the user before any write operation** (create, edit, comment, transition).
- Always get a fresh OAuth access token before KB or case API calls.
- Epic children: JQL `"Epic Link" = EPIC-KEY` (not `parentEpic`).
- KB is read-only. Jira and cases support read and write.
