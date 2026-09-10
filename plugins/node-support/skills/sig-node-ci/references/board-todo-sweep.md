# SIG Node CI Board: To-do → In-progress Sweep

Keep the 'Issues - To do' lane of the SIG Node CI/Test project board (https://github.com/orgs/kubernetes/projects/151, org: kubernetes, project number: 151) honest: a To-do card whose issue already has an assignee is being worked on and belongs in 'Issues - In progress'. This is the "keep the in-progress lanes current" step of the documented triage process (see board-triage.md).

## Rule

- **MOVE** a card from 'Issues - To do' to 'Issues - In progress' when the card's `assignees` list is non-empty.
- **LEAVE** it in 'Issues - To do' when `assignees` is `null`/empty.
- **FLAG (do not move)** a card in 'Issues - In progress' that has no assignee — surface it so the user can decide whether it went stale; moving cards backwards is a human call.
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
5. **Tally**: e.g. "4 to move, 9 stay in To do (unassigned), 1 in-progress card has no assignee".

## Quality Control

- **Never use `gh project item-delete`** on this board; this sweep only ever changes Status.
- If `field-list` shows the lane names or Status options have changed, adapt to the real names rather than assuming 'Issues - To do' / 'Issues - In progress'.
- If `--limit 500` returns exactly 500 items, raise the limit — the board may be larger than one page.
- Cards in 'Triage' are out of scope here even if assigned; they go through board-triage.md first.
