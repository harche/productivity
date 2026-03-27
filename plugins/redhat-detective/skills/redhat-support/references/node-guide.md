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

**Shorthand:** In this doc, `jira.sh` means `${CLAUDE_PLUGIN_ROOT}/scripts/jira.sh`.

### Standup Prep

"What's on my plate? What should I report?"

1. **My sprint items** — what I'm working on this sprint
   → [node-board.md](node-board.md): `jira.sh sprint-issues <SPRINT_ID> 100` (pipe through jq to filter by assignee)

2. **My open bugs** — bugs assigned to me
   → [node-bugs.md](node-bugs.md): `filter = "Node Bugs" AND assignee = currentUser() AND status not in (Done, CLOSED, Verified)`

3. **My epics** — feature work I own
   → [node-epics.md](node-epics.md): `project = OCPNODE AND issuetype = Epic AND assignee = currentUser() AND status not in (Closed, Done)`

4. **Items I'm watching** — bugs/issues I'm keeping an eye on
   → [node-bugs.md](node-bugs.md): use the "My" tab: `assignee = currentUser() OR watcher in (currentUser())`

5. **Composite shortcut** — all of the above in one call
   → `jira.sh my-standup-data <team>`

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

6. **Composite shortcut** — full bug overview in one call
   → `jira.sh bug-overview <team>`

### Investigation

"Dig into this issue. What's going on with OCPBUGS-12345?"

Follow these steps to build a complete picture:

1. **Deep dive** — full issue + comments + linked issues in one call
   → [jira.md](jira.md): `jira.sh issue-deep-dive OCPBUGS-12345`

2. **View the issue** — summary, status, assignee, description
   → [jira.md](jira.md): `jira.sh get OCPBUGS-12345`

3. **Read comments** — discussion, root cause analysis, workarounds
   → [jira.md](jira.md): `jira.sh comments OCPBUGS-12345`

4. **Find the parent epic** — broader context
   → [jira.md](jira.md): look for Epic Link in the issue fields, then view the epic

5. **Search Knowledge Base** — existing solutions or known issues
   → [knowledge-base.md](../knowledge-base.md): extract key error messages or symptoms from the bug and search KB

6. **Check support cases** — if SFDC Cases Links field is populated, look up the case
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
   → run search with priority filters: Blocker, Critical, Major

5. **Epic completion** — are the planned features done?
   → [node-epics.md](node-epics.md): `project = OCPNODE AND issuetype = Epic AND fixVersion = "4.22.0" AND status not in (Closed, Done)`

6. **Composite shortcut** — full release readiness in one call
   → `jira.sh release-data <team> [version]`

### Reporting

"How many bugs are open? Give me a summary."

```bash
# Total open Node bugs
jira.sh search 'filter = "Node Bugs" AND status not in (Done, CLOSED, Verified)' 1

# Open bugs by priority (run each separately)
jira.sh search 'filter = "Node Bugs" AND priority = Blocker AND status not in (Done, CLOSED, Verified)' 1
jira.sh search 'filter = "Node Bugs" AND priority = Critical AND status not in (Done, CLOSED, Verified)' 1
jira.sh search 'filter = "Node Bugs" AND priority = Major AND status not in (Done, CLOSED, Verified)' 1

# Customer-impacting bugs
jira.sh search 'filter = "Node Bugs" AND ("Customer Impact" = "Customer Escalated" OR "SFDC Cases Counter" is not EMPTY) AND status not in (Done, CLOSED, Verified)' 50

# Bugs by component (e.g., CRI-O)
jira.sh search 'filter = "Node Bugs" AND Component in ("Node / CRI-O") AND status not in (Done, CLOSED, Verified)' 50
```

Present counts in a summary table when the user asks for a report or overview.
