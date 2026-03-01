# Issues

View, create, update, and manage Jira issues.

## View Issue

```bash
# Basic issue details
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}?fields=summary,status,assignee,priority,issuetype,description,created,updated,components,labels,fixVersions,versions,reporter,resolution,resolutiondate,duedate" \
  | python3 -m json.tool

# All fields (large response)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}" \
  | python3 -m json.tool

# With field name mappings (useful for discovering custom field names)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}?expand=names" \
  | python3 -m json.tool

# With changelog (issue history)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}?expand=changelog" \
  | python3 -m json.tool

# Rendered fields (description/comments as HTML)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}?expand=renderedFields&fields=description,comment" \
  | python3 -m json.tool
```

## Epic Children

**Use `"Epic Link"` in JQL** — the `parentEpic` function does NOT work on this instance.

```bash
# Get all stories/tasks under an epic
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/search?jql=%22Epic+Link%22%3D{epicKey}&fields=summary,status,assignee,issuetype,priority&maxResults=50" \
  | python3 -m json.tool
```

## Comments

```bash
# List comments
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}/comment" \
  | python3 -m json.tool

# List comments with pagination
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}/comment?startAt=0&maxResults=10" \
  | python3 -m json.tool

# Add a comment (ALWAYS confirm with user first)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://issues.redhat.com/rest/api/2/issue/{issueKey}/comment" \
  -d '{"body": "Comment text here"}' \
  | python3 -m json.tool
```

## Transitions (Workflow)

```bash
# List available transitions for an issue
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}/transitions" \
  | python3 -m json.tool

# Perform a transition (ALWAYS confirm with user first)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://issues.redhat.com/rest/api/2/issue/{issueKey}/transitions" \
  -d '{"transition": {"id": "TRANSITION_ID"}}' \
  | python3 -m json.tool
```

Note: Some issues (especially Bugzilla-synced bugs) may return empty transitions if the workflow is managed externally.

## Update Issue

```bash
# Update fields (ALWAYS confirm with user first)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X PUT "https://issues.redhat.com/rest/api/2/issue/{issueKey}" \
  -d '{
    "fields": {
      "summary": "Updated summary",
      "description": "Updated description",
      "assignee": {"name": "username@redhat.com"},
      "priority": {"name": "Major"},
      "labels": ["label1", "label2"]
    }
  }'

# Update a single field
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X PUT "https://issues.redhat.com/rest/api/2/issue/{issueKey}" \
  -d '{"fields": {"assignee": {"name": "username@redhat.com"}}}'
```

## Create Issue

```bash
# Create a new issue (ALWAYS confirm with user first)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://issues.redhat.com/rest/api/2/issue" \
  -d '{
    "fields": {
      "project": {"key": "OCPNODE"},
      "issuetype": {"name": "Story"},
      "summary": "Issue summary",
      "description": "Detailed description",
      "assignee": {"name": "username@redhat.com"},
      "priority": {"name": "Major"},
      "customfield_12311140": "EPIC-KEY"
    }
  }' | python3 -m json.tool
```

Common issue types: `Epic`, `Story`, `Task`, `Bug`, `Sub-task`, `Feature`, `Spike`

## Link Issues

```bash
# Create a link between issues (ALWAYS confirm with user first)
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://issues.redhat.com/rest/api/2/issueLink" \
  -d '{
    "type": {"name": "Blocks"},
    "inwardIssue": {"key": "OCPNODE-100"},
    "outwardIssue": {"key": "OCPNODE-200"}
  }'
```

Common link types: `Blocks`, `Cloners`, `Duplicate`, `Relates`

## Watchers

```bash
# Get watchers
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}/watchers" \
  | python3 -m json.tool

# Add yourself as a watcher
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://issues.redhat.com/rest/api/2/issue/{issueKey}/watchers" \
  -d '"username@redhat.com"'
```

## Useful Custom Fields

These are Red Hat-specific custom fields available on issues.redhat.com:

| Custom Field ID | Name | Notes |
|---|---|---|
| `customfield_12311140` | Epic Link | Set on children to link to parent epic |
| `customfield_12311141` | Epic Name | Short name for the epic |
| `customfield_12311142` | Epic Status | Epic-specific status |
| `customfield_12310940` | Sprint | Sprint association |
| `customfield_12310243` | Story Points | Estimation points |
| `customfield_12313140` | Parent Link | Parent issue link |
| `customfield_12313240` | Team | Team assignment |
| `customfield_12313941` | Target start | Planned start date |
| `customfield_12313942` | Target end | Planned end date |
| `customfield_12315948` | QA Contact | QA assignee |
| `customfield_12316142` | Severity | Bug severity |
| `customfield_12318341` | Feature Link | Link to parent feature |
| `customfield_12319940` | Target Version | Target release version |
| `customfield_12320845` | Color Status | RAG status |
| `customfield_12316840` | Bugzilla Bug | Linked Bugzilla ID |
| `customfield_12317313` | Release Note Text | Release note content |
| `customfield_12316749` | Architect | Architect contact |
| `customfield_12316752` | Product Manager | PM contact |
| `customfield_12310220` | Git Pull Request | Linked PRs |
| `customfield_12316542` | Ready | Ready for development |
| `customfield_12316543` | Blocked | Blocked flag |
| `customfield_12316544` | Blocked Reason | Reason for block |

### Fetching Custom Fields

```bash
# Include specific custom fields in the response
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}?fields=summary,status,customfield_12311140,customfield_12310243,customfield_12319940" \
  | python3 -m json.tool

# Discover all field names for an issue
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://issues.redhat.com/rest/api/2/issue/{issueKey}?expand=names" \
  | python3 -c "import sys,json; data=json.load(sys.stdin); [print(f'{k}: {v}') for k,v in sorted(data.get('names',{}).items())]"
```
