# Node Board & Sprints

> For domain context and workflows, see [node-guide.md](node-guide.md). For bug queries, see [node-bugs.md](node-bugs.md). For epics, see [node-epics.md](node-epics.md).

Board, sprint, and saved filter reference for the OpenShift Node team.

## Board

The main board is **"Node board" (ID 7845)**, a scrum board covering OCPNODE + OCPKUEUE + Node-component bugs.

```bash
# Board details
acli jira board get --id 7845

# Active sprints
acli jira board list-sprints --id 7845 --state active

# Closed sprints
acli jira board list-sprints --id 7845 --state closed
```

## Sprints

Each sprint has a numeric ID shown by `list-sprints`. Use it to query sprint items.

```bash
# List items in a sprint
acli jira sprint list-workitems --sprint <SPRINT_ID> --board 7845

# Sprint items filtered by JQL
acli jira sprint list-workitems --sprint <SPRINT_ID> --board 7845 --jql 'assignee = currentUser()'

# Sprint details
acli jira sprint view --id <SPRINT_ID>
```

Active sprint names follow the pattern: `OCP Node Core Sprint N`, `OCP Node Devices Sprint N`, `OCP Kueue Sprint N`, etc.

## Other Boards

| ID | Name | Type |
|---|---|---|
| 7845 | Node board | scrum |
| 4383 | Node-Epics | kanban |
| 9874 | Node QE | scrum |

## Saved Filters

Key filters usable in JQL via `filter = "Name"`:

| Name | ID | Scope |
|---|---|---|
| Node Components | 91645 | Component list (Node, CRI-O, Kubelet, etc.) |
| Node Bugs | 83963 | Node component bugs in OCPBUGS/RHOCPPRIO/OCPNODE |
| Node Green Team | 89708 | Green team assignees |
| Node Blue Team | 64253 | Blue team assignees |
| Node Core Team | 66331 | `membersOf(OpenShift-Node-Team)` |
| Node Epics | 96318 | OCPNODE epics |
| Node CR bugs | 94401 | Component regression bugs |

```bash
# Look up a filter's JQL by ID
acli jira filter get --id 83963 --json
```
