# Node Bugs

> For domain context and workflows, see [node-guide.md](node-guide.md). For boards and sprints, see [node-board.md](node-board.md).

Bug triage dashboard for the OpenShift Node team.

All queries use the saved filter `"Node Bugs"` as a base, which scopes to Node components in OCPBUGS/RHOCPPRIO + OCPNODE bugs, excluding Obsolete/Won't Fix.

## Filter Tabs

Append these clauses: `filter = "Node Bugs" AND <clause>`.

| Tab | JQL Clause |
|-----|-----------|
| Untriaged | `priority = Undefined OR "Release Blocker" = Proposed OR assignee in ("aos-node@redhat.com")` |
| Triaged | `status in (NEW, "To Do") AND priority not in (Undefined) AND ("Release Blocker" not in (Proposed) OR "Release Blocker" is EMPTY) AND assignee not in (unassigned_jira, "aos-node@redhat.com")` |
| Refined | `status in (ASSIGNED, POST, Modified) AND priority not in (Undefined)` |
| Verification Needed | `status in (ON_QA) AND priority not in (Undefined)` |
| Escape Analysis Needed | `("Customer Impact" = "Customer Escalated" OR "SFDC Cases Counter" is not EMPTY) AND status not in (NEW, "To Do", ASSIGNED) AND "Escape Reason" is EMPTY AND created >= 2025-01-01` |
| Blocker? | `"Release Blocker" = Proposed OR priority = Blocker AND "Release Blocker" is EMPTY` |
| Blocker+ | `"Release Blocker" = Approved OR priority = Blocker` |
| Customer Issues | `"Customer Impact" = "Customer Escalated" OR "SFDC Cases Counter" is not EMPTY` |
| Escalations | `project = "Red Hat OpenShift Priority List" OR "Customer Impact" = "Customer Escalated" OR labels in (shift_telco5g)` |
| ! CVE | `labels not in (SecurityTracking) AND issuetype not in (Vulnerability, Weakness)` |
| CVE | `labels in (SecurityTracking) OR issuetype in (Vulnerability, Weakness)` |
| Older than 100d | `created <= -100d` |
| My | `assignee = currentUser() OR watcher in (currentUser())` |
| Kueue | `Component in ("Node / Kueue")` |
| CR (Component Regression) | `labels = component-regression` |

## Modifiers

Combine with any tab clause using `AND`:

```
AND fixVersion = "4.22.0"                            # specific version
AND fixVersion is EMPTY                              # no version set
AND status not in (Done, CLOSED, Obsolete, "Won't Fix / Obsolete", Verified)  # open only
AND priority in (Blocker, Critical)                  # high priority
AND assignee = currentUser()                         # my bugs
AND created <= -100d                                 # older than 100 days
AND due <= 7d                                        # CVEs due this week
AND "Special Handling" in (contract-priority)        # contract priority
AND filter = "Node Green Team"                       # green team
AND filter = "Node Blue Team"                        # blue team
AND filter = "Node Core Team"                        # core team
```

## Examples

```bash
# Untriaged bugs for 4.22
acli jira workitem search --jql 'filter = "Node Bugs" AND (priority = Undefined OR "Release Blocker" = Proposed OR assignee in ("aos-node@redhat.com")) AND fixVersion = "4.22.0" AND status not in (Done, CLOSED, Verified) ORDER BY priority DESC' --limit 50

# Blocker+ bugs
acli jira workitem search --jql 'filter = "Node Bugs" AND ("Release Blocker" = Approved OR priority = Blocker) AND status not in (Done, CLOSED, Verified) ORDER BY priority DESC' --limit 50

# Customer issues older than 100 days
acli jira workitem search --jql 'filter = "Node Bugs" AND ("Customer Impact" = "Customer Escalated" OR "SFDC Cases Counter" is not EMPTY) AND created <= -100d AND status not in (Done, CLOSED, Verified) ORDER BY created ASC' --limit 50

# My escalations
acli jira workitem search --jql 'filter = "Node Bugs" AND (project = "Red Hat OpenShift Priority List" OR "Customer Impact" = "Customer Escalated" OR labels in (shift_telco5g)) AND assignee = currentUser() AND status not in (Done, CLOSED, Verified) ORDER BY priority DESC' --limit 50

# CVEs due this week
acli jira workitem search --jql 'filter = "Node Bugs" AND (labels in (SecurityTracking) OR issuetype in (Vulnerability, Weakness)) AND status not in (Done, CLOSED, Verified, ON_QA) AND due <= 7d ORDER BY due ASC' --limit 50

# My open bugs by version
acli jira workitem search --jql 'filter = "Node Bugs" AND assignee = currentUser() AND status not in (Done, CLOSED, Verified) ORDER BY fixVersion ASC, priority DESC' --limit 50

# Contract priority without fix version
acli jira workitem search --jql 'filter = "Node Bugs" AND "Special Handling" in (contract-priority) AND fixVersion is EMPTY AND status not in (Done, CLOSED, Verified, ON_QA) ORDER BY priority DESC' --limit 50

# Green team blockers
acli jira workitem search --jql 'filter = "Node Bugs" AND ("Release Blocker" = Approved OR priority = Blocker) AND filter = "Node Green Team" AND status not in (Done, CLOSED, Verified) ORDER BY priority DESC' --limit 50

# Component regression bugs
acli jira workitem search --jql 'filter = "Node Bugs" AND labels = component-regression AND status not in (Done, CLOSED, Verified) ORDER BY priority DESC' --limit 50
```
