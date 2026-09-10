# SIG Node CI Reference Index

Upstream Kubernetes SIG Node CI workflows. All of them are recommend-only toward upstream repos: report findings and print ready-to-run commands; never create/edit issues, PRs, or board items without explicit user approval.

Root: `./`

## Workflows

|board-triage.md — triage the SIG Node CI/Test project board (kubernetes project 151): keep/remove calls for Triage-column items
|board-todo-sweep.md — sweep the 'Issues - To do' and 'Issues - In progress' columns: move assigned To-do cards to In progress, detect and close duplicate cards (closed dupes → Archive-it), flag In-progress cards with no assignee, nudge/unassign stale In-progress assignees
|pr-reviewer-finder.md — for cards in 'PRs - Needs Reviewer': gate out cards that are not reviewer-blocked (red CI, hold, rebase, superseded, waiting on author), then find the most suitable reviewers from engagement, OWNERS, active directory reviewers, git history, and KEP authors; draft a /cc comment with the reason
|testgrid-review.md — weekly TestGrid review: find FAILING jobs via the JSON API, cluster by root cause, check/draft kubernetes/kubernetes tracking issues
