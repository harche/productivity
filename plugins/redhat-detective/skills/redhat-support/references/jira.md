# Jira (redhat.atlassian.net)

> For Node team-specific queries, start with [node-guide.md](node-guide.md) instead.

All Jira operations use `acli`. Run `acli jira workitem -h` for the full command list.

## View

```bash
acli jira workitem view OCPNODE-4151
acli jira workitem view OCPNODE-4151 --json
acli jira workitem view OCPNODE-4151 --fields '*all' --json
acli jira workitem view OCPNODE-4151 --fields "summary,status,assignee,priority,description,comment"
```

## Search

```bash
acli jira workitem search --jql 'project = OCPNODE AND type = Epic' --limit 10
acli jira workitem search --jql 'project = OCPNODE AND type = Epic' --json
acli jira workitem search --jql 'project = OCPNODE AND type = Epic' --csv
acli jira workitem search --jql 'project = OCPNODE AND type = Epic' --paginate  # fetch all
acli jira workitem search --jql 'project = OCPNODE AND type = Epic' --count     # count only
```

Use `--fields` to control output columns (default: `issuetype,key,assignee,priority,status,summary`).

## Epic Children

```bash
acli jira workitem search --jql '"Epic Link" = OCPNODE-4151' --fields "key,summary,status,assignee,priority"
```

## Comments

```bash
acli jira workitem comment list --key OCPNODE-4151
acli jira workitem comment create --key OCPNODE-4151 --body "Comment text"
# See: acli jira workitem comment -h
```

## Transitions

```bash
acli jira workitem transition --key OCPNODE-4151 --status "In Progress"
# See: acli jira workitem transition -h
```

## Create

```bash
acli jira workitem create --project OCPNODE --type Story --summary "Issue summary" --assignee "@me"
acli jira workitem create --project OCPNODE --type Story --summary "Title" --description "Details" --parent OCPNODE-4151
# See: acli jira workitem create -h
```

Common issue types: `Epic`, `Story`, `Task`, `Bug`, `Sub-task`, `Feature`, `Spike`

## Edit

```bash
acli jira workitem edit --key OCPNODE-4151 --summary "Updated summary"
acli jira workitem edit --key OCPNODE-4151 --assignee "user@redhat.com"
acli jira workitem edit --key OCPNODE-4151 --labels "label1,label2"
# See: acli jira workitem edit -h
```

## Assign

```bash
acli jira workitem assign --key OCPNODE-4151 --assignee "@me"
acli jira workitem assign --key OCPNODE-4151 --assignee "user@redhat.com"
# See: acli jira workitem assign -h
```

## Link

```bash
acli jira workitem link create --out OCPNODE-100 --in OCPNODE-200 --type Blocks
acli jira workitem link list --key OCPNODE-4151
acli jira workitem link type  # list available link types
# See: acli jira workitem link -h
```

## Watchers

```bash
acli jira workitem watcher list --key OCPNODE-4151
# See: acli jira workitem watcher -h
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

## curl Fallbacks

ACLI cannot update custom fields (sprint, labels via custom field, etc.) on existing issues. Use `curl` with the API token from Keychain for these operations:

```bash
JIRA_API_TOKEN=$(security find-generic-password -s "JIRA_API_TOKEN" -w)

# Move issue to a sprint
curl -s -u "harpatil@redhat.com:$JIRA_API_TOKEN" \
  -X POST "https://redhat.atlassian.net/rest/agile/1.0/sprint/{sprintId}/issue" \
  -H "Content-Type: application/json" \
  -d '{"issues": ["OCPNODE-4137"]}'

# Update a custom field on an existing issue
curl -s -u "harpatil@redhat.com:$JIRA_API_TOKEN" \
  -X PUT "https://redhat.atlassian.net/rest/api/2/issue/{issueKey}" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"customfield_10855": {"name": "4.22.0"}}}'

# Add a watcher (also not supported by ACLI)
curl -s -u "harpatil@redhat.com:$JIRA_API_TOKEN" \
  -X POST "https://redhat.atlassian.net/rest/api/2/issue/{issueKey}/watchers" \
  -H "Content-Type: application/json" \
  -d '"accountId"'
```

Auth: Basic auth with `email:API_TOKEN`. Token stored in macOS Keychain as `JIRA_API_TOKEN`.

## Custom Fields

Key Red Hat custom fields (use field names in JQL, IDs for `--fields`):

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
