# SIG Node CI Board: To-do / In-progress Sweep

Keep the 'Issues - To do' lane of the SIG Node CI/Test project board (https://github.com/orgs/kubernetes/projects/151, org: kubernetes, project number: 151) honest: a To-do card whose issue already has an assignee is being worked on and belongs in 'Issues - In progress'. This is the "keep the in-progress lanes current" step of the documented triage process (see board-triage.md).

## Rule

- **MOVE** a card from 'Issues - To do' to 'Issues - In progress' when the card's `assignees` list is non-empty.
- **LEAVE** it in 'Issues - To do' when `assignees` is `null`/empty.
- **FLAG (do not move)** a card in 'Issues - In progress' that has no assignee — surface it so the user can decide whether it went stale; moving cards backwards is a human call.
- **DUPLICATE check before any MOVE.** Compare To-do cards pairwise on test name + job + author; if two match, verify the root cause and recommend closing the older/narrower one (see *Duplicate Cards* below). A card whose issue was closed as a duplicate goes to **'Archive-it'**, never 'Done'.
- **STALE check** every card in 'Issues - In progress' that has an assignee: if the assignee has shown no activity for longer than the threshold, recommend a nudge comment, or an unassign if a nudge already went unanswered. See *Stale In-progress Cards* below.
- Scope is **issues only**. PRs live in the 'PRs - *' lanes and use reviewer/author state, not assignment; do not touch them here.

An assignee is the only signal. Do not infer "in progress" from linked PRs, comments, or labels — the board owners assign when they pick up work, and that is the convention this sweep enforces.

## Workflow

1. **List the board once and cache it.** One call gives everything needed — `assignees` and `status` are top-level fields on every item, so no per-issue `gh issue view` is required. The board holds ~1300 items, so use a high limit and save to a file; the project GraphQL API rate-limits heavy item-list calls even when `gh api rate_limit` still shows budget, so reuse the file for the rest of the session:
   `gh project item-list 151 --owner kubernetes --format json --limit 2000 > board.json`
   Pull `.items[] | select(.content.type == "Issue")` and bucket by `.status`:
   - `"Issues - To do"` with `assignees` non-empty → MOVE candidates
   - `"Issues - To do"` with `assignees` null/empty → leave, list only in the tally
   - `"Issues - In progress"` with `assignees` null/empty → FLAG
2. **Resolve the real IDs** (same as board-triage.md): project ID (`PVT_...`) from `gh project view 151 --owner kubernetes --format json`; Status field ID (`PVTSSF_...`) and the 'Issues - In progress' option ID from `gh project field-list 151 --owner kubernetes --format json`; each card's item ID (`PVTI_...`) is the `id` in the item-list output. Never emit `<placeholder>` IDs you could have resolved.
3. **Duplicate pass** over the To-do lane (see *Duplicate Cards*), before recommending any move.
4. **Prow-command sanity check.** While reading each candidate issue's comments, flag malformed Prow commands that silently did nothing — e.g. `/triage accept` (should be `/triage accepted`) or `/priority imporant-soon` — and print the corrected comment. These leave the issue without `triage/accepted` / `priority/*` labels.
5. **Report.** One table for MOVE candidates (issue number, title, assignees) and one for FLAGged in-progress cards with no assignee. State the unassigned To-do count in the tally rather than listing every card.
6. **Recommend-only, always print the commands.** Do not run any `gh project item-edit` unless the user explicitly asks. For every MOVE candidate print:
   `gh project item-edit --id <ITEM_ID> --project-id <PROJECT_ID> --field-id <STATUS_FIELD_ID> --single-select-option-id <IN_PROGRESS_OPTION_ID>`
   in a copy-pasteable block keyed by issue number. If the user approves, run them and re-list the board to confirm the status changed.
7. **Stale pass** over 'Issues - In progress' cards with assignees (see below), reported as its own table.
8. **Tally**: e.g. "4 to move, 9 stay in To do (unassigned), 1 duplicate pair, 1 in-progress card has no assignee, 2 in-progress cards stale (1 nudge, 1 unassign)".

## Duplicate Cards

The same flake gets filed twice more often than you would expect (seen: k/k #141614 and #141786, same author, same assignee, same job, near-identical titles, neither referencing the other). Moving both to In progress just doubles the noise.

**Detect.** Within the To-do lane, pair cards that share two or more of: the same test name in "Which tests are flaking/failing?", the same TestGrid link or job name, the same author, the same assignee, or a title that differs only by a word. `gh issue view <NUM> --json title,body,author,assignees` on the candidates is enough.

**Verify before calling it a duplicate.** Same title is not proof. Confirm the same failure signature: the same assertion line in the example runs (e.g. `expected number of restarts: 0, found restarts: 1`) and the same root cause in the node logs. For a prow run, take the GCS path from the issue's example link, fetch `artifacts/<node>/kubelet.log`, and grep for the failing pod name from `build-log.txt`. Two issues with the same assertion but different kubelet-side causes are not duplicates.

**Recommend.** Keep the newer or superset issue (the one covering more variants, or with k8s-triage links); close the older/narrower one. Draft the closing comment with the reason, a pointer to the survivor, the one-line root cause, and `/close` on its own last line, so Prow closes it:
`gh issue comment <OLD> --repo kubernetes/kubernetes --body $'Closing as a duplicate of #<NEW>, which covers the same test on the same job (<one-line root cause>). Tracking continues there.\n/close'`
Verify afterwards with `gh issue view <OLD> --json state,stateReason` (expect CLOSED / COMPLETED).

**Lane for the closed duplicate: 'Archive-it', never 'Done'.** Done means the tracked problem was fixed; a duplicate closed with no fix is noise. The survivor's card follows the normal assignee rule. Print the move:
`gh project item-edit --id <OLD_ITEM_ID> --project-id <PROJECT_ID> --field-id <STATUS_FIELD_ID> --single-select-option-id <ARCHIVE_IT_OPTION_ID>`
Board IDs as of 2026-09 (re-check with `gh project field-list 151 --owner kubernetes --format json` if any edit fails): project `PVT_kwDOAM_34M4AURf4`; Status field `PVTSSF_lADOAM_34M4AURf4zgM87lc`; options Issues - To do `fd8421e5`, Issues - In progress `975693a6`, Done `05887be2`, Archive-it `0bc92ec1`.

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
- If `--limit N` returns exactly N items, raise the limit — the board has ~1300 items and `--limit 500` silently truncates.
- Confirm a Status move with `gh api graphql -f query='{ node(id:"<ITEM_ID>") { ... on ProjectV2Item { fieldValueByName(name:"Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } } } } }'` rather than re-listing the whole board.
- Cards in 'Triage' are out of scope here even if assigned; they go through board-triage.md first.
- The stale pass costs a few `gh` calls per in-progress card; if the lane is large, offer to run it only for cards older than the threshold by `updatedAt` first.
