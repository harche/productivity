# SIG Node CI Board: To-do / In-progress Sweep

Keep the 'Issues - To do' lane of the SIG Node CI/Test project board (https://github.com/orgs/kubernetes/projects/151, org: kubernetes, project number: 151) honest: a To-do card whose issue already has an assignee is being worked on and belongs in 'Issues - In progress'. This is the "keep the in-progress lanes current" step of the documented triage process (see board-triage.md).

## Rule

- **MOVE** a card from 'Issues - To do' to 'Issues - In progress' when the card's `assignees` list is non-empty.
- **LEAVE** it in 'Issues - To do' when `assignees` is `null`/empty.
- **FLAG (do not move)** a card in 'Issues - In progress' that has no assignee — surface it so the user can decide whether it went stale; moving cards backwards is a human call.
- **STALE check** every card in 'Issues - In progress' that has an assignee: if the assignee has shown no activity for longer than the threshold, recommend a nudge comment, or an unassign if a nudge already went unanswered. See *Stale In-progress Cards* below.
- Scope is **issues only**. PRs live in the 'PRs - *' lanes and use reviewer/author state, not assignment; do not touch them here.

An assignee is the only signal. Do not infer "in progress" from linked PRs, comments, or labels — the board owners assign when they pick up work, and that is the convention this sweep enforces.

## Workflow

1. **List the board.** One call gives everything needed — `assignees` and `status` are top-level fields on every item, so no per-issue `gh issue view` is required:
   `gh project item-list 151 --owner kubernetes --format json --limit 500`
   Pull `.items[] | select(.content.type == "Issue")` and bucket by `.status`:
   - `"Issues - To do"` with `assignees` non-empty → MOVE candidates
   - `"Issues - To do"` with `assignees` null/empty → leave, list only in the tally
   - `"Issues - In progress"` with `assignees` null/empty → FLAG
2. **Resolve the real IDs** (same as board-triage.md): project ID (`PVT_...`) from `gh project view 151 --owner kubernetes --format json`; Status field ID (`PVTSSF_...`) and the 'Issues - In progress' option ID from `gh project field-list 151 --owner kubernetes --format json`; each card's item ID (`PVTI_...`) is the `id` in the item-list output. Never emit `<placeholder>` IDs you could have resolved.
3. **Report.** One table for MOVE candidates (issue number, title, assignees) and one for FLAGged in-progress cards with no assignee. State the unassigned To-do count in the tally rather than listing every card.
4. **Recommend-only, always print the commands.** Do not run any `gh project item-edit` unless the user explicitly asks. For every MOVE candidate print:
   `gh project item-edit --id <ITEM_ID> --project-id <PROJECT_ID> --field-id <STATUS_FIELD_ID> --single-select-option-id <IN_PROGRESS_OPTION_ID>`
   in a copy-pasteable block keyed by issue number. If the user approves, run them and re-list the board to confirm the status changed.
5. **Stale pass** over 'Issues - In progress' cards with assignees (see below), reported as its own table.
6. **Tally**: e.g. "4 to move, 9 stay in To do (unassigned), 1 in-progress card has no assignee, 2 in-progress cards stale (1 nudge, 1 unassign)".

## Stale In-progress Cards

Assigned does not mean attended. An in-progress card whose assignee has gone quiet blocks anyone else from picking the work up. Evaluate each assigned 'Issues - In progress' card and recommend one of NUDGE, UNASSIGN, or ACTIVE.

**Threshold.** Default 30 days of assignee inactivity. Let the user override ("stale after 14 days"). A nudge counts as unanswered after 14 days.

**Gather per card** (repo is `.content.repository` from item-list; usually kubernetes/kubernetes, sometimes kubernetes/test-infra):
- Last assignee activity on the issue: `gh issue view <NUM> --repo <REPO> --json updatedAt,assignees,comments` — take the newest `comments[]` entry whose `author.login` is an assignee.
- When they were assigned: `gh api repos/<REPO>/issues/<NUM>/timeline --paginate --jq '[.[] | select(.event=="assigned") | {who:.assignee.login, at:.created_at}] | last'`. A fresh assignment with no comment yet is NOT stale; measure from the later of assignment date and last assignee comment.
- Open PRs by the assignee for this issue: `gh search prs --repo <REPO> --author <LOGIN> --state open "<NUM>"`; also count any PR that mentions the issue in `comments[]` bodies. If such a PR exists, check its `updatedAt` — an open PR that was pushed within the threshold means ACTIVE even if the issue itself is quiet.
- Whether a nudge was already posted: look for a prior comment (by anyone) asking the assignee if they are still working on it, and its date.

**Decide:**
- **ACTIVE** — assignee comment, assignment, or PR push within the threshold. No action.
- **NUDGE** — quiet for longer than the threshold and no earlier nudge. Recommend a comment; draft it so the user can paste it:
  `gh issue comment <NUM> --repo <REPO> --body $'@<LOGIN> are you still working on this? It has been quiet for <N> days. If not, please `/unassign` so someone else can pick it up. No worries either way.'`
- **UNASSIGN** — a nudge was posted 14+ days ago with no reply from the assignee and no PR movement. Recommend both the unassign and moving the card back to 'Issues - To do':
  `gh issue comment <NUM> --repo <REPO> --body $'/unassign @<LOGIN>\nUnassigning after no response to the check-in above so this is open for anyone to pick up. Feel free to re-assign yourself if you are still on it.'`
  `gh project item-edit --id <ITEM_ID> --project-id <PROJECT_ID> --field-id <STATUS_FIELD_ID> --single-select-option-id <TODO_OPTION_ID>`
  (`/unassign` via a Prow comment works for anyone; `gh issue edit <NUM> --remove-assignee <LOGIN>` needs triage rights on the repo.)

**Report** a table: issue, assignee, days since last assignee activity, evidence (last comment date / assigned date / open PR), verdict. Judgment beats the number: a long-running rebase, a KEP-gated change, or an assignee who is a known maintainer mid-release should lean ACTIVE or at most NUDGE — say why. Commenting on someone's issue is outward-facing: never post a nudge or unassign without the user's explicit go-ahead, and never unassign without a prior nudge.

## Quality Control

- **Never use `gh project item-delete`** on this board; this sweep only ever changes Status.
- If `field-list` shows the lane names or Status options have changed, adapt to the real names rather than assuming 'Issues - To do' / 'Issues - In progress'.
- If `--limit 500` returns exactly 500 items, raise the limit — the board may be larger than one page.
- Cards in 'Triage' are out of scope here even if assigned; they go through board-triage.md first.
- The stale pass costs a few `gh` calls per in-progress card; if the lane is large, offer to run it only for cards older than the threshold by `updatedAt` first.
