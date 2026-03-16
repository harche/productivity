# Node Epics & Features

> For domain context and workflows, see [node-guide.md](node-guide.md). For boards and sprints, see [node-board.md](node-board.md).

Epic and feature tracking for the OpenShift Node team (OCPNODE project).

## Epics

```bash
# All open epics
acli jira workitem search --jql 'project = OCPNODE AND issuetype = Epic AND status not in (Closed, Done) ORDER BY priority DESC, updated DESC' --limit 30

# My epics
acli jira workitem search --jql 'project = OCPNODE AND issuetype = Epic AND assignee = currentUser() AND status not in (Closed, Done) ORDER BY priority DESC' --limit 20

# Epic children (stories/tasks under an epic)
acli jira workitem search --jql '"Epic Link" = OCPNODE-4151' --fields "key,summary,status,assignee,priority"

# Epics by version
acli jira workitem search --jql 'project = OCPNODE AND issuetype = Epic AND fixVersion = "4.22.0" AND status not in (Closed, Done) ORDER BY priority DESC' --limit 30

# Recently closed epics
acli jira workitem search --jql 'project = OCPNODE AND issuetype = Epic AND status in (Closed, Done) AND resolved >= -30d ORDER BY resolved DESC' --limit 20
```

## Stories, Tasks & Spikes

```bash
# Open stories/tasks in OCPNODE
acli jira workitem search --jql 'project = OCPNODE AND issuetype in (Story, Task, Spike) AND status not in (Closed, Done) ORDER BY priority DESC' --limit 30

# My open work items
acli jira workitem search --jql 'project = OCPNODE AND assignee = currentUser() AND status not in (Closed, Done) ORDER BY priority DESC' --limit 30

# Items in code review
acli jira workitem search --jql 'project = OCPNODE AND status = "Code Review" ORDER BY updated DESC' --limit 20

# Unassigned items
acli jira workitem search --jql 'project = OCPNODE AND assignee is EMPTY AND status not in (Closed, Done) ORDER BY priority DESC' --limit 20
```

## Kueue

```bash
# Open Kueue items
acli jira workitem search --jql 'project = OCPKUEUE AND status not in (Closed, Done) ORDER BY priority DESC' --limit 30

# Kueue epics
acli jira workitem search --jql 'project = OCPKUEUE AND issuetype = Epic AND status not in (Closed, Done) ORDER BY priority DESC' --limit 20
```
