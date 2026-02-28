# Search (JQL)

Search for issues using Jira Query Language (JQL).

## Basic Search

```bash
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/search?jql=<URL-ENCODED-JQL>&fields=summary,status,assignee,priority,issuetype&maxResults=20" \
  | python3 -m json.tool
```

**Tip:** URL-encode JQL queries. Use `+` for spaces, `%3D` for `=`, `%27` for `'`, `%22` for `"`.

## Pagination

The search API returns paginated results:

```json
{
  "startAt": 0,
  "maxResults": 20,
  "total": 147,
  "issues": [...]
}
```

```bash
# First page
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/search?jql=project%3DOCPNODE&startAt=0&maxResults=20&fields=summary,status" \
  | python3 -m json.tool

# Next page
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/search?jql=project%3DOCPNODE&startAt=20&maxResults=20&fields=summary,status" \
  | python3 -m json.tool
```

## JQL Syntax

### Operators

| Operator | Example |
|---|---|
| `=` | `status = "In Progress"` |
| `!=` | `status != Done` |
| `IN` | `status IN ("To Do", "In Progress")` |
| `NOT IN` | `priority NOT IN (Blocker, Critical)` |
| `IS EMPTY` | `assignee IS EMPTY` |
| `IS NOT EMPTY` | `fixVersion IS NOT EMPTY` |
| `~` (contains) | `summary ~ "kubernetes"` |
| `>`, `<`, `>=`, `<=` | `created >= "2026-01-01"` |
| `WAS` | `status WAS "In Progress"` |
| `CHANGED` | `status CHANGED FROM "To Do" TO "In Progress"` |

### Logical Operators

```
project = OCPNODE AND type = Epic AND status = "In Progress"
project = OCPNODE AND (status = "To Do" OR status = "New")
project = OCPBUGS AND NOT status = Done
```

### Sorting

```
ORDER BY priority DESC, updated DESC
ORDER BY created ASC
ORDER BY status ASC, assignee ASC
```

## Common Queries

### By Project and Type

```bash
# All epics in a project
jql: project = OCPNODE AND type = Epic

# All bugs in a project
jql: project = OCPBUGS AND type = Bug

# Features in a project
jql: project = OCPSTRAT AND type = Feature
```

### By Assignee

```bash
# My issues
jql: assignee = currentUser()

# Assigned to a specific person
jql: assignee = "username@redhat.com"

# Unassigned issues
jql: assignee IS EMPTY AND project = OCPNODE
```

### By Status

```bash
# Open issues (not resolved)
jql: project = OCPNODE AND resolution = Unresolved

# In progress
jql: project = OCPNODE AND status = "In Progress"

# Recently resolved
jql: project = OCPNODE AND resolved >= -7d
```

### By Date

```bash
# Created this week
jql: project = OCPNODE AND created >= startOfWeek()

# Updated in last 7 days
jql: project = OCPNODE AND updated >= -7d

# Created in a date range
jql: project = OCPNODE AND created >= "2026-01-01" AND created <= "2026-02-28"

# Due soon
jql: project = OCPNODE AND duedate <= 7d AND duedate >= 0d
```

### By Component and Label

```bash
# By component
jql: project = OCPBUGS AND component = "Management Console"

# By label
jql: project = OCPNODE AND labels = "tech-debt"

# Multiple labels
jql: project = OCPNODE AND labels IN ("ci", "testing")
```

### By Version

```bash
# Issues targeting a specific fix version
jql: project = OCPNODE AND fixVersion = "4.22"

# Issues affecting a version
jql: project = OCPBUGS AND affectedVersion = "4.19"
```

### Epic-Related

```bash
# Children of a specific epic
jql: "Epic Link" = OCPNODE-4151

# Epics with no children
jql: project = OCPNODE AND type = Epic AND issueFunction NOT IN hasLinks("Epic Link")

# Epics by status
jql: project = OCPNODE AND type = Epic AND status = "In Progress" ORDER BY priority DESC
```

### Text Search

```bash
# Search in summary
jql: project = OCPNODE AND summary ~ "conformance"

# Search in description
jql: project = OCPNODE AND description ~ "kubernetes"

# Search in summary or description
jql: project = OCPNODE AND text ~ "TLS profile"
```

### Combined Queries

```bash
# My open epics, ordered by priority
jql: assignee = currentUser() AND type = Epic AND resolution = Unresolved ORDER BY priority DESC

# Critical/blocker bugs updated recently
jql: project = OCPBUGS AND type = Bug AND priority IN (Blocker, Critical) AND updated >= -7d ORDER BY priority DESC

# Unresolved issues in a sprint
jql: sprint in openSprints() AND project = OCPNODE AND resolution = Unresolved
```

## Field Selection

Use `fields=` to limit response size (comma-separated):

```bash
# Minimal: just key and summary
fields=summary

# Standard view
fields=summary,status,assignee,priority,issuetype,created,updated

# With custom fields
fields=summary,status,assignee,customfield_12311140,customfield_12310243

# All fields (large response, avoid in searches)
# Omit the fields parameter entirely
```

## Response Format

Use `python3` to extract specific data from search results:

```bash
# List issues as a table
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/search?jql=project%3DOCPNODE+AND+type%3DEpic&maxResults=10&fields=summary,status,assignee,priority" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total: {data[\"total\"]} issues')
print(f'{\"Key\":<20} {\"Status\":<15} {\"Assignee\":<25} {\"Summary\"}')
print('-' * 90)
for issue in data['issues']:
    f = issue['fields']
    assignee = f.get('assignee', {})
    print(f'{issue[\"key\"]:<20} {f[\"status\"][\"name\"]:<15} {(assignee or {}).get(\"displayName\", \"Unassigned\"):<25} {f[\"summary\"][:50]}')
"
```
