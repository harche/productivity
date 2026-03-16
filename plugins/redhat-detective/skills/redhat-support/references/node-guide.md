# Node Team Guide

Domain knowledge and workflows for the OpenShift Node team. Read this first for any Node-related query, then follow the links to specific references.

## Contents

- [Components](#components) — what the Node team owns
- [Projects](#projects) — Jira projects
- [Jira Workflow](#jira-workflow) — status meanings
- [Workflows](#workflows) — standup, triage, investigation, release readiness, reporting

---

## Components

The Node team owns these Jira components (defined in the saved filter "Node Components"):

| Component | What it is |
|---|---|
| Node | General node / kubelet |
| Node / CRI-O | Container runtime (OCI-compliant) |
| Node / Kubelet | Core kubelet functionality |
| Node / CPU manager | CPU pinning and allocation |
| Node / Memory manager | Memory allocation and NUMA |
| Node / Topology manager | NUMA-aware resource alignment |
| Node / Numa aware Scheduling | NUMA scheduling policies |
| Node / Device Manager | Device plugin framework |
| Node / Pod resource API | Pod resource allocation queries |
| Node / Node Problem Detector | Node health monitoring |
| Node / Kueue | Job queueing and quota management |
| Node / Instaslice-operator | Dynamic GPU/accelerator slicing |

When the user mentions CRI-O, kubelet, device manager, DRA, Kueue, etc., map to the appropriate component using `Component in ("Node / CRI-O")` in JQL.

## Projects

| Project | What it tracks |
|---|---|
| OCPNODE | Node team epics, stories, tasks, spikes |
| OCPBUGS | Cross-team bug tracker (filter by Node components) |
| RHOCPPRIO | Red Hat OpenShift Priority List (escalations) |
| OCPKUEUE | Kueue-specific work |
| OCPSTRAT | Strategy/feature tracking |

## Jira Workflow

Bug lifecycle statuses and what they mean:

| Status | Meaning |
|---|---|
| NEW | Just filed, no one has looked at it |
| To Do | Acknowledged, not started |
| ASSIGNED | Developer is working on it |
| POST | Patch submitted (PR open) |
| Modified | Fix merged |
| ON_QA | Awaiting QA verification |
| Verified | QA confirmed the fix |
| CLOSED / Done | Resolved |
| Obsolete | No longer relevant |
| Won't Fix / Obsolete | Declined |

Feature/epic statuses:

| Status | Meaning |
|---|---|
| New | Not started |
| Planning | Being scoped |
| To Do | Ready for development |
| In Progress | Active development |
| Code Review | PR under review |
| Review | Broader review (design, arch) |
| Dev Complete | Code done, not yet tested |
| Done / Closed | Complete |

Key fields:

| Field | Meaning |
|---|---|
| Priority: Undefined | Untriaged — needs prioritization |
| Release Blocker: Proposed | Someone thinks this blocks the release |
| Release Blocker: Approved | Confirmed release blocker |
| Customer Impact: Customer Escalated | Customer-reported or escalated issue |
| SFDC Cases Counter (not EMPTY) | Has linked support cases |
| Special Handling: contract-priority | Contractual obligation |

## Sub-teams

| Team | Filter | Focus |
|---|---|---|
| Core | `filter = "Node Core Team"` | Kubelet, CRI-O, runtime |
| Green | `filter = "Node Green Team"` | Subset of core |
| Blue | `filter = "Node Blue Team"` | Subset of core |

Sprint names: `OCP Node Core Sprint N`, `OCP Node Devices Sprint N`, `OCP Kueue Sprint N`, `CNF Compute Sprint N`

---

## Workflows

### Standup Prep

"What's on my plate? What should I report?"

1. **My sprint items** — what I'm working on this sprint
   → [node-board.md](node-board.md): `acli jira sprint list-workitems --sprint <ID> --board 7845 --jql 'assignee = currentUser()'`

2. **My open bugs** — bugs assigned to me
   → [node-bugs.md](node-bugs.md): `filter = "Node Bugs" AND assignee = currentUser() AND status not in (Done, CLOSED, Verified)`

3. **My epics** — feature work I own
   → [node-epics.md](node-epics.md): `project = OCPNODE AND issuetype = Epic AND assignee = currentUser() AND status not in (Closed, Done)`

4. **Items I'm watching** — bugs/issues I'm keeping an eye on
   → [node-bugs.md](node-bugs.md): use the "My" tab: `assignee = currentUser() OR watcher in (currentUser())`

### Bug Triage

"What needs attention? What's untriaged?"

1. **Untriaged bugs** — no priority set, or blocker proposals, or assigned to the team queue
   → [node-bugs.md](node-bugs.md): Untriaged tab

2. **Blocker proposals** — someone flagged these as potential release blockers
   → [node-bugs.md](node-bugs.md): Blocker? tab

3. **Escalations** — customer-impacting or priority-list items
   → [node-bugs.md](node-bugs.md): Escalations tab

4. **By version** — scope triage to a specific release
   → [node-bugs.md](node-bugs.md): add `AND fixVersion = "4.22.0"`

5. **By component** — e.g., just CRI-O bugs
   → add `AND Component in ("Node / CRI-O")` to any query

### Investigation

"Dig into this issue. What's going on with OCPBUGS-12345?"

Follow these steps to build a complete picture:

1. **View the issue** — summary, status, assignee, description
   → [jira.md](jira.md): `acli jira workitem view OCPBUGS-12345`

2. **Read comments** — discussion, root cause analysis, workarounds
   → [jira.md](jira.md): `acli jira workitem comment list --key OCPBUGS-12345`

3. **Check history** — who changed what, when was it moved to POST
   → [jira.md](jira.md): `acli jira workitem view OCPBUGS-12345 --fields '*all' --json` (check changelog)

4. **Check linked issues** — duplicates, blockers, related work
   → [jira.md](jira.md): `acli jira workitem link list --key OCPBUGS-12345`

5. **Find the parent epic** — broader context
   → [jira.md](jira.md): look for Epic Link in the issue fields, then view the epic

6. **Search Knowledge Base** — existing solutions or known issues
   → [knowledge-base.md](../knowledge-base.md): extract key error messages or symptoms from the bug and search KB

7. **Check support cases** — if SFDC Cases Links field is populated, look up the case
   → [cases.md](../cases.md): fetch the case number from the field

### Release Readiness

"Are we clear for 4.22? Any blockers?"

1. **Approved blockers** — must-fix before release
   → [node-bugs.md](node-bugs.md): Blocker+ tab with `AND fixVersion = "4.22.0"`

2. **Proposed blockers** — pending triage decision
   → [node-bugs.md](node-bugs.md): Blocker? tab with `AND fixVersion = "4.22.0"`

3. **CVEs due soon** — security vulnerabilities with approaching deadlines
   → [node-bugs.md](node-bugs.md): CVE tab with `AND due <= 14d`

4. **Open bug count by priority** — overall picture
   → run `--count` with priority filters: Blocker, Critical, Major

5. **Epic completion** — are the planned features done?
   → [node-epics.md](node-epics.md): `project = OCPNODE AND issuetype = Epic AND fixVersion = "4.22.0" AND status not in (Closed, Done)`

### Reporting

"How many bugs are open? Give me a summary."

Use `--count` for aggregation:

```bash
# Total open Node bugs
acli jira workitem search --jql 'filter = "Node Bugs" AND status not in (Done, CLOSED, Verified)' --count

# Open bugs by priority (run each separately)
acli jira workitem search --jql 'filter = "Node Bugs" AND priority = Blocker AND status not in (Done, CLOSED, Verified)' --count
acli jira workitem search --jql 'filter = "Node Bugs" AND priority = Critical AND status not in (Done, CLOSED, Verified)' --count
acli jira workitem search --jql 'filter = "Node Bugs" AND priority = Major AND status not in (Done, CLOSED, Verified)' --count

# Open bugs for a specific version
acli jira workitem search --jql 'filter = "Node Bugs" AND fixVersion = "4.22.0" AND status not in (Done, CLOSED, Verified)' --count

# Customer-impacting bugs
acli jira workitem search --jql 'filter = "Node Bugs" AND ("Customer Impact" = "Customer Escalated" OR "SFDC Cases Counter" is not EMPTY) AND status not in (Done, CLOSED, Verified)' --count

# Bugs by component (e.g., CRI-O)
acli jira workitem search --jql 'filter = "Node Bugs" AND Component in ("Node / CRI-O") AND status not in (Done, CLOSED, Verified)' --count
```

Present counts in a summary table when the user asks for a report or overview.
