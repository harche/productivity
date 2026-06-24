# SIG Node CI Board Triage

Triage the Kubernetes SIG Node CI/Test project board (https://github.com/orgs/kubernetes/projects/151, org: kubernetes, project number: 151). For each item in the board's 'Triage' column, decide whether it belongs on this board and should be accepted, or does not belong and should be removed.

## Core Principle: What This Board Is For

This board is EXCLUSIVELY for issues and PRs about the **CI tests of SIG Node** — not SIG Node features or product behavior in general. An item can be a perfectly legitimate SIG Node issue and still NOT belong here if it has no CI/test angle.

## The Acceptance Rule

The SIG Node CI subproject documents its triage process in the CI meeting agenda; the board's dashboard view is https://github.com/orgs/kubernetes/projects/151/views/1. The documented steps are: (1) add all open issues/PRs matching the card-source queries (see *Card Sources* below) to the Triage column; (2) **Archive** every Triage card that is NOT in scope of the SIG Node CI group; (3) move in-scope **issues → 'Issues - To do'** and in-scope **PRs → a PR-review lane**, then keep the in-progress lanes current.

Your core judgment is step 2 — deciding what is "in scope of the SIG Node CI group." In-scope items fall into four buckets:

**KEEP** the item if its *substance* is one of:
1. **Failing / flaking SIG Node tests or CI jobs** — by far the largest bucket. Titles like [Failing Test], [Flaking Test], [Flake], "Failure cluster ...", "job X failing/stuck/timing out".
2. **SIG Node test-coverage gaps** — proposals to add or improve test coverage (integration, e2e, unit) for SIG Node areas.
3. **SIG Node test/CI infrastructure** — job/lane renaming, CI migrations (e.g., containerd v2, CRI-O), dropping cgroupv1 jobs, naming-convention audits, image/job config restructuring (including kubernetes/test-infra items).
4. **Bugs surfaced by or affecting SIG Node test reliability** — e.g., goroutine leaks found in _test.go files, kubelet panics caught by a failing test.

**REMOVE** the item if it is a SIG Node feature/behavior/product change with **no CI-test angle** — even if it is a legitimate SIG Node issue. Examples: feature-gate GA promotions, production-code refactors in pkg/kubelet/..., kubelet behavior bug fixes that are not tied to a failing/flaking test, test failure, coverage gap, or CI infrastructure.

## Critical Caveats

- **Grade labels by provenance — don't blanket-distrust them.** Bot/auto-applied labels (`area/test`, `sig/testing`, `kind/failing-test` stamped for merely touching a `_test.go` file) are low-confidence; judge those on **substance** — read the title, body, and what the change actually does. BUT a **`sig/node` (or node-relevant `area/test`) applied manually by any human** — to an issue OR a PR, via a `/sig`/`/area` comment or a direct non-bot label edit — is a deliberate categorization and a **strong KEEP signal**. Weight it higher still when the applier is a maintainer/chair, but never *require* that. Your topic-ownership reasoning is a prior, not evidence: when a manual `sig/node` signal exists, it overrides that prior.
- **Cross-SIG suspicion — but defer to explicit human routing.** Watch for items whose substance is sig-scheduling/DRA, sig-apps, sig-api-machinery, or control-plane work even when they carry test-related labels. If the test/feature is owned by another SIG, it likely does not belong on the SIG Node CI board. **Guardrail:** if a human has manually routed the item (issue or PR) to SIG Node (`/sig node`), do NOT confidently REMOVE on a topic-ownership hunch — your topic prior and an explicit human signal are in conflict, so KEEP, or at most flag BORDERLINE and surface the conflict for the user's call.
- **Removal mechanics.** Rejected items are **moved to 'Archive-it'** by changing their Status (a `gh project item-edit` status change) — they are NOT deleted from the board. This is the board owners' actual workflow: select 'Archive-it' from the Status dropdown on the item. **Never use `gh project item-delete`** — this is the official SIG Node board and items must be preserved, not destroyed. Accepting an item = moving it out of Triage into its destination lane: issues → 'Issues - To do', PRs → a PR-review lane.

## Board Structure Reference

The Status single-select field options are: Triage, Issues - To do, Issues - In progress, PRs - Needs Reviewer/Approver/Waiting on Author, Done, Archive-it. There is a written doc the project anchors to (referenced by umbrella issue #134862): kubernetes/test-infra/config/jobs/kubernetes/sig-node/README.md — but it governs test-job naming/lane structure, NOT board triage.

## Card Sources (how items reach the board)

Per the documented process, Triage cards are added from saved searches for open items carrying a SIG Node test signal, filtered to exclude items already on the board:
- **kubernetes/test-infra**, label `sig/node` — PRs and Issues.
- **kubernetes/kubernetes**, label `area/test` — PRs and Issues.
- **kubernetes/kubernetes**, label `kind/failing-test` — PRs and Issues.

Adding cards is normally done by the board maintainers; your primary job is triaging items already sitting in the Triage column. If asked to find candidates to add, reconstruct these with `gh search issues`/`gh search prs` using the `label:` filters above and exclude items already on the board.

## Workflow

1. **Confirm scope.** The user may want issues only, PRs only, or both. If unclear, ask. Default to whatever the user specifies.
2. **Gather data with `gh`.** Use the GitHub CLI exclusively for board access. Useful commands:
   - `gh project item-list 151 --owner kubernetes --format json --limit <N>` to list items.
   - `gh project field-list 151 --owner kubernetes --format json` to confirm field/status structure.
   - `gh issue view <num> --repo kubernetes/kubernetes --json title,body,labels,state,comments` and `gh pr view <num> --repo <repo> --json title,body,labels,files,state,comments` to inspect substance. For test-infra items use `--repo kubernetes/test-infra`. **Always fetch `comments` and scan the comment/event timeline — for issues AND PRs — for manual `/sig` and `/area` slash commands and who issued them**; these are deliberate human routing decisions and the highest-value scope signal. Note: k8s-ci-robot is the account that *stamps* the resulting label, so judging by the label-event actor will wrongly read "auto-applied" — the human `/sig`/`/area` comment is the true signal.
   - Filter to items whose Status is 'Triage'.
3. **Assess each item one by one.** For every Triage item, read enough of its substance to apply the rule. Classify as **KEEP**, **REMOVE**, or **BORDERLINE** (when SIG ownership of the test/framework is genuinely unclear). Also note the item's current Prow triage state — whether it still has `needs-triage`/`needs-priority` vs. already carries `triage/accepted` and a `priority/*` label — so that for KEEPs you only suggest the `/triage accepted` + `/priority` comment when it hasn't already been applied. (These `triage/*`/`priority/*` labels are legitimate STATE signals; the earlier "do not trust labels" caveat is specifically about `area/test`/`sig/testing`/`kind/failing-test` for the keep/remove decision.)
4. **Report.** Present recommendations in clear, grouped tables: Clear KEEP, Clear REMOVE, and Borderline. For each item give: number, title, one-line substance-based justification, and the bucket number for KEEPs. For BORDERLINE items, state your lean and the precise tension/question that needs the user's domain call.
5. **Recommend-only by default, but ALWAYS print the commands.** Do NOT execute any board mutation unless the user explicitly asks you to act. However, regardless of whether you are asked to act, your report MUST include a ready-to-run `gh` command for the recommended action on every item, so the user can copy-paste and perform it themselves. This is a hard requirement — never leave the user to construct commands by hand.
   - **Fetch the real IDs first.** To build working commands you need: the **project ID** (`PVT_...`), each item's **item ID** (`PVTI_...`), the **Status field ID** (`PVTSSF_...`), and the **single-select option IDs** for Triage / Issues - To do / the PR-review lanes / Archive-it. Get item IDs from `gh project item-list 151 --owner kubernetes --format json` (each item has an `id`); get the project ID and field/option IDs from `gh project field-list 151 --owner kubernetes --format json` and `gh project view 151 --owner kubernetes --format json`. Fill these REAL values into the commands — never emit `<placeholder>` IDs if you can resolve them.
   - **Provide the command matching each item's recommendation, plus the obvious alternatives**, clearly labeled by action:
     - **Accept (keep on board)** → this is TWO actions: (a) apply the Prow triage commands on the issue/PR itself, AND (b) move the board card out of Triage into its destination lane — per the documented process, **issues → 'Issues - To do'** and **PRs → a PR-review lane** (default 'PRs - Needs Reviewer'; use 'PRs - Needs Approver' if it already has lgtm, or 'PRs Waiting on Author' if it needs author changes). Both (a) and (b) are part of acceptance — do not omit (a).
       (a) Prow comments on the item (this is what sets `triage/accepted` + `priority/*` and clears the `needs-triage`/`needs-priority` labels):
       `gh issue comment <NUM> --repo kubernetes/kubernetes --body $'/triage accepted\n/priority <LEVEL>'`  (use `gh pr comment` for PRs; use `--repo kubernetes/test-infra` for test-infra items)
       where `<LEVEL>` is one of `important-soon` (CI broken / blocking), `important-longterm` (flakes, persistent test gaps), or `backlog` (lower-urgency coverage/cleanup). Suggest a level per item but let the user confirm — priority is a judgment call.
       (b) Move the card to its destination lane (use the 'Issues - To do' option for issues, or the matching PR-review-lane option for PRs):
       `gh project item-edit --id <ITEM_ID> --project-id <PROJECT_ID> --field-id <STATUS_FIELD_ID> --single-select-option-id <DEST_OPTION_ID>`
     - **Remove (reject)** → move the card's Status to 'Archive-it'. This is how the board owners remove an item from active triage — a Status change, NOT a hard delete. **Never use `gh project item-delete` on this board**; items must be preserved:
       `gh project item-edit --id <ITEM_ID> --project-id <PROJECT_ID> --field-id <STATUS_FIELD_ID> --single-select-option-id <ARCHIVE_IT_OPTION_ID>`
   - Present these as a copy-pasteable block (e.g., a fenced code block per item or a grouped "commands to run" section keyed by item number). If you genuinely cannot resolve an ID, say so explicitly and show the command with a clearly-marked placeholder and the lookup needed to fill it.
   - Only run a mutating command yourself after the user explicitly approves. **Never run `gh project item-delete` against this board** — it is the official SIG Node board; removal is always a move to 'Archive-it' via `item-edit`.
6. **Surface a tally** (e.g., "5 keep, 3 remove, 3 borderline") and close by flagging the borderline domain calls and reminding the user of removal mechanics.

## Quality Control

- Never recommend KEEP or REMOVE based on auto-applied labels alone — always cite the substance. EXCEPTION: a `sig/node` label a human applied manually (via `/sig node` on an issue or PR) is itself substantive scope evidence — never confidently REMOVE such an item; at most flag BORDERLINE, and name who applied the routing and how.
- When a PR is a cherry-pick or a multi-part series, judge the underlying change, not the PR mechanics.
- If you cannot determine SIG ownership of a test framework or component, classify as BORDERLINE rather than guessing.
- If `gh` returns unexpected structure (field renamed, options changed), re-run `field-list` and adapt rather than assuming the structure above.
- Be concise and decision-oriented; the user wants actionable keep/remove calls, not exhaustive prose.
