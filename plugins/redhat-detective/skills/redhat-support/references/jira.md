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

IMPORTANT: Jira Cloud uses ADF (Atlassian Document Format). Plain text via `--body` renders as one unformatted paragraph. Wiki markup (`*bold*`, `{quote}`) renders as literal characters. Always use ADF JSON via `--body-file` for formatted comments.

```bash
# List comments
acli jira workitem comment list --key OCPNODE-4151

# Create comment with ADF (write JSON to temp file first)
acli jira workitem comment create --key OCPNODE-4151 --body-file /tmp/comment.json

# Update last comment by same author
acli jira workitem comment create --key OCPNODE-4151 --edit-last --body-file /tmp/comment.json

# Simple unformatted comment (only for short, single-paragraph text)
acli jira workitem comment create --key OCPNODE-4151 --body "Simple one-liner"

# See: acli jira workitem comment -h
```

### ADF JSON Template

Write this to a temp file, then pass via `--body-file`:

```json
{"version":1,"type":"doc","content":[
  {"type":"heading","attrs":{"level":3},"content":[
    {"type":"text","text":"Section Title"}
  ]},
  {"type":"paragraph","content":[
    {"type":"text","text":"Normal text. "},
    {"type":"text","text":"Bold text","marks":[{"type":"strong"}]},
    {"type":"text","text":". "},
    {"type":"text","text":"Link text","marks":[{"type":"link","attrs":{"href":"https://example.com"}}]}
  ]},
  {"type":"blockquote","content":[
    {"type":"paragraph","content":[
      {"type":"text","text":"Quoted text","marks":[{"type":"em"}]}
    ]}
  ]},
  {"type":"bulletList","content":[
    {"type":"listItem","content":[
      {"type":"paragraph","content":[{"type":"text","text":"Item 1"}]}
    ]},
    {"type":"listItem","content":[
      {"type":"paragraph","content":[{"type":"text","text":"Item 2"}]}
    ]}
  ]},
  {"type":"codeBlock","attrs":{"language":"bash"},"content":[
    {"type":"text","text":"echo hello"}
  ]}
]}
```

### ADF Marks Reference
- Bold: `"marks":[{"type":"strong"}]`
- Italic: `"marks":[{"type":"em"}]`
- Code (inline): `"marks":[{"type":"code"}]`
- Link: `"marks":[{"type":"link","attrs":{"href":"URL"}}]`
- Strikethrough: `"marks":[{"type":"strike"}]`

### ADF Node Types
`heading` (attrs: level 1-6), `paragraph`, `bulletList`, `orderedList`, `listItem`, `blockquote`, `codeBlock` (attrs: language), `table`, `tableRow`, `tableHeader`, `tableCell`

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
