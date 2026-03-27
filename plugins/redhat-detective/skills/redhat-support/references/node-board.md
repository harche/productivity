# Node Board & Sprints

> For domain context and workflows, see [node-guide.md](node-guide.md). For bug queries, see [node-bugs.md](node-bugs.md). For epics, see [node-epics.md](node-epics.md).

Board, sprint, and saved filter reference for the OpenShift Node team.

**Shorthand:** In this doc, `jira.sh` means `${CLAUDE_PLUGIN_ROOT}/scripts/jira.sh`.

## Board

The main board is **"Node board" (ID 7845)**, a scrum board covering OCPNODE + OCPKUEUE + Node-component bugs.

## Sprints

```bash
# Active sprints
jira.sh sprints active

# Closed sprints
jira.sh sprints closed

# Future sprints
jira.sh sprints future

# List items in a sprint
jira.sh sprint-issues <SPRINT_ID> 100

# Start a sprint
jira.sh start-sprint <SPRINT_ID>

# Close a sprint
jira.sh close-sprint <SPRINT_ID>
```

### Move issue to a sprint

```bash
jira.sh move-to-sprint <SPRINT_ID> OCPNODE-4137
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
