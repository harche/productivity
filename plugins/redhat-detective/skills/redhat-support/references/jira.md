# Jira (redhat.atlassian.net)

> For Node team-specific queries, start with [node-guide.md](node-guide.md) instead.

All Jira operations use the bundled `jira.sh` CLI. It wraps the Jira REST API v3 with curl and handles auth via macOS Keychain.

**Shorthand:** In this doc, `jira.sh` means `${CLAUDE_PLUGIN_ROOT}/scripts/jira.sh`.

## View

```bash
# Full issue details (JSON)
jira.sh get OCPNODE-4151

# Deep dive — issue + comments (ADF→text) + linked issues
jira.sh issue-deep-dive OCPNODE-4151
```

## Search

```bash
# Search with JQL (default limit: 50)
jira.sh search 'project = OCPNODE AND type = Epic' 10

# All results use JSON output by default
```

## Epic Children

```bash
jira.sh search '"Epic Link" = OCPNODE-4151' 50
```

## Comments

```bash
# List comments
jira.sh comments OCPNODE-4151

# Add a comment (plain text)
jira.sh comment "This is a comment" OCPNODE-4151

# Comment on multiple issues
jira.sh comment "Blocking on upstream fix" OCPNODE-100 OCPNODE-200
```

## Transitions

```bash
# List available transitions
jira.sh transitions OCPNODE-4151

# Perform a transition (use transition ID from above)
jira.sh transition 31 OCPNODE-4151

# Comment + close in one step
jira.sh close "Fixed in PR #123" OCPNODE-4151
```

## Links

```bash
# Add a remote link (e.g., GitHub PR)
jira.sh link OCPNODE-4151 "https://github.com/org/repo/pull/123" "PR #123: Fix description"

# GitHub URLs auto-detect and add the GitHub favicon icon
```

## Fields

```bash
# Set story points
jira.sh set-points OCPNODE-4151 5

# Set any field (string, number, or JSON value)
jira.sh set-field OCPNODE-4151 customfield_10855 '{"name": "4.22.0"}'

# Move issue to a sprint
jira.sh move-to-sprint <SPRINT_ID> OCPNODE-4151 OCPNODE-4152
```

## Sprints

```bash
# List sprints (active|future|closed)
jira.sh sprints active

# Get issues in a sprint
jira.sh sprint-issues <SPRINT_ID> 100
```

## Composite Commands

High-level commands that aggregate multiple API calls:

```bash
# Sprint dashboard — issues by status, workload, blockers
jira.sh sprint-dashboard <team>

# Standup prep — dashboard + recent updates + new bugs
jira.sh standup-data <team>

# Bug triage — untriaged, unassigned, blockers, new
jira.sh bug-overview <team>

# Carryover report — not-done items with context
jira.sh carryover-report <team>

# Planning — carryovers + backlog + bugs
jira.sh planning-data <team>

# Release readiness — blockers, bugs, epics
jira.sh release-data <team> [version]

# Per-member sprint items + comment counts
jira.sh team-activity <team>

# My board items
jira.sh my-board-data <team>

# My bugs
jira.sh my-bugs-data <team>

# My standup data
jira.sh my-standup-data <team>

# Epic progress
jira.sh epic-progress <EPIC-KEY>

# Pickup candidates
jira.sh pickup-data <team>
```

## Health Check

```bash
# Validate custom field IDs against Jira metadata
jira.sh health-check
```

## JQL Reference

### Operators

| Operator | Example |
|---|---|
| `=`, `!=` | `status = "In Progress"` |
| `IN`, `NOT IN` | `status IN ("To Do", "In Progress")` |
| `IS EMPTY`, `IS NOT EMPTY` | `assignee IS EMPTY` |
| `~` (contains) | `summary ~ "kubernetes"` |
| `>`, `<`, `>=`, `<=` | `created >= "2026-01-01"` |
| `WAS` | `status WAS "In Progress"` |
| `CHANGED` | `status CHANGED FROM "To Do" TO "In Progress"` |

### Common Queries

```
assignee = currentUser() AND type = Epic AND resolution = Unresolved ORDER BY priority DESC
"Epic Link" = OCPNODE-4151
project = OCPBUGS AND type = Bug AND priority IN (Blocker, Critical) AND updated >= -7d
project = OCPNODE AND text ~ "TLS profile"
project = OCPNODE AND fixVersion = "4.22"
project = OCPNODE AND created >= startOfWeek()
sprint in openSprints() AND project = OCPNODE AND resolution = Unresolved
```

### Unsupported JQL

`issueFunction` (e.g. `issueFunction in commented("by currentUser()")`) does **not** exist on Jira Cloud. There is no native JQL to filter by commenter.

**Workaround — find issues I commented on:**

Jira Cloud auto-adds you as a watcher when you comment. Use `watcher = currentUser()` with text/comment search:

```
watcher = currentUser() AND comment ~ "keyword" ORDER BY updated DESC
```

## Custom Fields

Key Red Hat custom fields (use field names in JQL, IDs for API calls):

| ID | Name |
|---|---|
| `customfield_10014` | Epic Link |
| `customfield_10011` | Epic Name |
| `customfield_10020` | Sprint |
| `customfield_10028` | Story Points |
| `customfield_10001` | Team |
| `customfield_10022` | Target start |
| `customfield_10023` | Target end |
| `customfield_10855` | Target Version |
| `customfield_10840` | Severity |
| `customfield_10847` | Release Blocker |
| `customfield_10877` | Bugzilla Bug |
| `customfield_10875` | Git Pull Request |
| `customfield_10467` | Architect |
| `customfield_10469` | Product Manager |
| `customfield_10470` | QA Contact |
| `customfield_10712` | Color Status |
| `customfield_10783` | Release Note Text |
| `customfield_10484` | Ready |
| `customfield_10517` | Blocked |
| `customfield_10483` | Blocked Reason |
| `customfield_10978` | SFDC Cases Counter |
| `customfield_10979` | SFDC Cases Links |
| `customfield_12313441` | SFDC Cases (legacy) |
