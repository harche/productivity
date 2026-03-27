# Node Epics & Features

> For domain context and workflows, see [node-guide.md](node-guide.md). For boards and sprints, see [node-board.md](node-board.md).

Epic and feature tracking for the OpenShift Node team (OCPNODE project).

**Shorthand:** In this doc, `jira.sh` means `${CLAUDE_PLUGIN_ROOT}/scripts/jira.sh`.

## Epics

```bash
# All open epics
jira.sh search 'project = OCPNODE AND issuetype = Epic AND status not in (Closed, Done) ORDER BY priority DESC, updated DESC' 30

# My epics
jira.sh search 'project = OCPNODE AND issuetype = Epic AND assignee = currentUser() AND status not in (Closed, Done) ORDER BY priority DESC' 20

# Epic children (stories/tasks under an epic)
jira.sh search '"Epic Link" = OCPNODE-4151' 50

# Epics by version
jira.sh search 'project = OCPNODE AND issuetype = Epic AND fixVersion = "4.22.0" AND status not in (Closed, Done) ORDER BY priority DESC' 30

# Recently closed epics
jira.sh search 'project = OCPNODE AND issuetype = Epic AND status in (Closed, Done) AND resolved >= -30d ORDER BY resolved DESC' 20

# Epic progress (composite — children + completion stats)
jira.sh epic-progress OCPNODE-4151
```

## Stories, Tasks & Spikes

```bash
# Open stories/tasks in OCPNODE
jira.sh search 'project = OCPNODE AND issuetype in (Story, Task, Spike) AND status not in (Closed, Done) ORDER BY priority DESC' 30

# My open work items
jira.sh search 'project = OCPNODE AND assignee = currentUser() AND status not in (Closed, Done) ORDER BY priority DESC' 30

# Items in code review
jira.sh search 'project = OCPNODE AND status = "Code Review" ORDER BY updated DESC' 20

# Unassigned items
jira.sh search 'project = OCPNODE AND assignee is EMPTY AND status not in (Closed, Done) ORDER BY priority DESC' 20
```

## Kueue

```bash
# Open Kueue items
jira.sh search 'project = OCPKUEUE AND status not in (Closed, Done) ORDER BY priority DESC' 30

# Kueue epics
jira.sh search 'project = OCPKUEUE AND issuetype = Epic AND status not in (Closed, Done) ORDER BY priority DESC' 20
```
