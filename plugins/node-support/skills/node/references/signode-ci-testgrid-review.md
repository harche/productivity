# SIG Node Weekly TestGrid Review

Weekly SIG Node CI health review: scan the SIG Node TestGrid dashboards for FAILING jobs, determine which failures already have a tracking issue in `kubernetes/kubernetes`, and draft new issues (from the official failing-test template) for those that don't.

**HARD SAFETY RULE — recommend-only.** This workflow NEVER creates, comments on, or edits issues/PRs in `kubernetes/kubernetes`, `kubernetes/test-infra`, or any upstream repo. All `gh` usage is read-only (`gh search`, `gh issue view`, `gh api` GETs). The deliverable is a report plus ready-to-run drafted `gh issue create` commands the user reviews and executes themselves. Only run a mutating command if the user explicitly approves that specific command in this session.

## Dashboards in scope

https://testgrid.k8s.io/sig-node is a dashboard **group** (it has no `/summary` endpoint — returns 404). The weekly review covers these member dashboards by default:

- `sig-node-release-blocking` (highest priority — release signal)
- `sig-node-kubelet`
- `sig-node-containerd`
- `sig-node-cri-o`

Other group members exist (`sig-node-presubmits`, `sig-node-dynamic-resource-allocation`, `sig-node-cri-tools`, etc.); include them only if the user asks. To enumerate current group members, scrape the group page: `curl -s https://testgrid.k8s.io/sig-node | grep -o '"sig-node[a-z-]*"' | sort -u`.

## Data source: TestGrid JSON API (do NOT use the UI)

TestGrid's UI is backed by plain JSON endpoints — use them directly:

1. **Per-dashboard summary** (one call gives every tab's status and its currently-failing tests):
   ```
   curl -s https://testgrid.k8s.io/<dashboard>/summary
   ```
   Returns a JSON object keyed by tab name. Fields per tab:
   - `overall_status` — `PASSING` | `FLAKY` | `FAILING` | `STALE` | `BROKEN` | `PENDING` | `ACCEPTABLE` | `""` (empty = no summary computed yet; skip these)
   - `status` — human string like `"Tab stats: 2 of 10 (20.0%) recent columns passed"`
   - `tests[]` — the rows with **active alerts** (only populated when FAILING). Each entry: `display_name`, `fail_count` (consecutive failures), `fail_timestamp` (epoch of first failure in the streak — this is "since when"), `pass_timestamp` (last pass), `failure_message` (truncated error from the latest failure), `linked_bugs[]` (issue numbers already linked in TestGrid — a strong "already tracked" signal)
   - `bug_url` — the issue tracker configured for that tab (`.../kubernetes/kubernetes/issues/` or `.../kubernetes/test-infra/issues/`) — use it to pick which repo the tracking issue belongs in
   - `dashboard_name`, `last_run_timestamp`, `latest_green`

2. **Per-tab table** (only needed to resolve the prow job name):
   ```
   curl -s "https://testgrid.k8s.io/<dashboard>/table?tab=<tab>&width=5" | jq -r '.query'
   ```
   `.query` is the GCS prefix, e.g. `kubernetes-ci-logs/logs/ci-node-crio-resource-managers` — the last path segment is the **prow job name**, and `https://prow.k8s.io/job-history/gs/<query>` is the job-history link. Tab name usually equals the job name minus a prefix, but don't assume — resolve it when drafting an issue.

Note: `https://testgrid.k8s.io/api/v1/...` is not served for this instance (404); the endpoints above are the working interface.

Convert epoch timestamps portably with jq (works on macOS and Linux): `jq -rn '<epoch> | todate'`.

## How TestGrid computes the status (so you never need the UI)

Verified from TestGrid source (`GoogleCloudPlatform/testgrid`: `pkg/updater/updater.go` `alertRow()`, `pkg/summarizer/summary.go` `overallStatus()`) and the Kubernetes defaults (`kubernetes/test-infra`: `config/testgrids/default.yaml`):

- A test row gets an **alert** after `num_failures_to_alert` **consecutive** failures — Kubernetes default **3**. The alert clears after `num_passes_to_disable_alert` consecutive passes — default **1**. `fail_count` in the summary is the current consecutive-failure streak; `fail_timestamp` is the streak's first failure.
- Tab status is evaluated over the `num_columns_recent` most recent **completed** runs — default **10** (running columns are skipped, which is why you may see fewer).
- Status precedence: **BROKEN** (fraction of failing cells in a column exceeds `broken_column_threshold`) → **STALE** (`alert_stale_results_hours` exceeded; k8s default 0 = disabled) → **FAILING** (≥1 row has an active alert) → **FLAKY** (no active alert, but ≥1 of the recent columns has any failing cell) → **PASSING** (all recent columns fully green).

Practical consequences:
- **FAILING = some test has failed ≥3 runs in a row and hasn't passed since.** That's the "consistently failing, needs a tracking issue" bar the weekly review cares about.
- **FLAKY = failures that never hit 3-in-a-row.** Report the FLAKY tally for awareness, but flakes generally don't get a fresh issue from this workflow unless the user asks (they're often better handled via existing flake issues / triage board).
- A single passing run resets the streak, so a tab can flip FAILING → FLAKY without anyone fixing anything — check `fail_timestamp` history before assuming a fix.

## Workflow

1. **Fetch all summaries and bucket the tabs.**
   ```bash
   for d in sig-node-release-blocking sig-node-kubelet sig-node-containerd sig-node-cri-o; do
     curl -s "https://testgrid.k8s.io/$d/summary" |
       jq -r --arg d "$d" 'to_entries[] | select(.value.overall_status=="FAILING") |
         "\($d)\t\(.key)\t\(.value.status)"'
   done
   ```
   Also collect the FLAKY list (same query with `=="FLAKY"`) for the report tally.
   - **Deduplicate by tab name** — the same job appears on multiple dashboards (e.g. `ci-node-e2e` is on both `sig-node-containerd` and `sig-node-release-blocking`). Track each job once, noting all dashboards it appears on; release-blocking membership raises priority.
   - **Separate `pull-*` tabs** (presubmit/canary jobs) from `ci-*`/periodic tabs. The weekly review's main target is periodic CI; report failing presubmit canaries in their own low-priority section.

2. **For each FAILING job, extract the failure details** from the summary entry's `tests[]`:
   - Failing test names (`display_name`), consecutive `fail_count`, since-when (`fail_timestamp | todate`), and `failure_message`.
   - **Job-level vs test-level failure:** if the failing rows are only `<tab>.Overall` / `kubetest2.Test` / `Test` (harness rows), the job itself is breaking (infra, image, boskos, timeout) rather than a specific test — the issue should be framed as a failing *job*. If real test rows alert alongside them, lead with those.
   - Resolve the prow job name and job-history link via the `table` endpoint's `.query` (step above), and fetch the latest failed run's link from `https://prow.k8s.io/job-history/gs/<query>` if deeper context is needed.

3. **Check whether the failure is already tracked.** In order:
   - `linked_bugs` in the summary entry — if non-empty, it's tracked; verify state with `gh issue view`.
   - Search `kubernetes/kubernetes` (and `kubernetes/test-infra` when `bug_url` points there) with several strategies, since titles vary:
     ```bash
     gh search issues --repo kubernetes/kubernetes --state open "<prow job name>" --json number,title,url,updatedAt --limit 10
     gh search issues --repo kubernetes/kubernetes --state open "<distinctive fragment of test name>" --json number,title,url,updatedAt --limit 10
     gh search issues --repo kubernetes/kubernetes --state open --label kind/failing-test --label sig/node --json number,title,url,updatedAt --limit 50
     ```
     Observed title conventions to match against: `[Failing Test] ...`, `Failure cluster [<hash>] ...` (auto-filed by triage tooling), and plain job-name titles. A recently-closed issue for the same job may mean a regression — mention it rather than treating the failure as untracked.
   - Classify each failing job: **TRACKED** (open issue found — link it), **REGRESSION?** (only a recently-closed issue found), or **UNTRACKED** (needs an issue).

4. **Cluster by root cause before drafting — one issue per cause, not per tab.** Failing tabs usually collapse into far fewer real problems (a live example: 18 FAILING tabs reduced to 5 clusters). Group UNTRACKED failures that share:
   - the same failing test set across sibling job variants (e.g. default / all-alpha / serial flavors of one suite), or
   - the same start window (`fail_timestamp` within hours) **plus** the same failure signature — especially harness-row-only failures (`kubetest.Up`, `kubetest.Node Tests`, `kubetest.Timeout`) pointing at a shared dependency such as a common image config or a runtime version bump.
   Draft ONE issue per cluster listing all affected jobs. Corollaries:
   - If a cluster's likely root cause already has a TRACKED issue that just doesn't name every affected job, prefer drafting a **comment** on that issue (adding the missing jobs) over a new issue — or reference it prominently in the new draft and say folding-in is an option for maintainers.
   - An outlier start date inside a cluster (one job failing a week earlier) is worth calling out in the draft rather than splitting the cluster on a hunch.

5. **Draft an issue for each UNTRACKED cluster** using the official template (`kubernetes/kubernetes` `.github/ISSUE_TEMPLATE/failing-test.yaml`, auto-labels `kind/failing-test`). Sections (use these exact headings in the body):
   - **Which jobs are failing?** — prow job name(s) + TestGrid tab link(s) (`https://testgrid.k8s.io/<dashboard>#<tab>`)
   - **Which tests are failing?** — the alerting `display_name`s (or "job-level failure, no individual test" for harness-row-only cases)
   - **Since when has it been failing?** — `fail_timestamp` as a UTC date + `fail_count` consecutive runs
   - **Testgrid link** — the tab URL
   - **Reason for failure (if possible)** — the `failure_message` excerpt, plus anything gleaned from the latest prow run
   - **Anything else we need to know?** — job-history link, other dashboards the job appears on, release-blocking status
   - **Relevant SIG(s)** — `/sig node`
   File against the repo indicated by the tab's `bug_url` (usually `kubernetes/kubernetes`; some tabs route to `kubernetes/test-infra`).

6. **Report — and stop.** Present:
   - A summary table of FAILING jobs grouped by cluster: jobs, dashboards, failing tests count, since-when, consecutive fails, tracking status with issue link or "UNTRACKED".
   - A one-line FLAKY tally per dashboard (names only).
   - For each UNTRACKED failure: the full drafted issue body, followed by a copy-pasteable command the **user** runs:
     ```bash
     gh issue create --repo kubernetes/kubernetes \
       --title "[Failing Test] <job or test summary>" \
       --label kind/failing-test --label sig/node \
       --body-file <drafted-body.md>
     ```
     Write each drafted body to a scratch file so the command is genuinely runnable. Do NOT execute it.

## Quality control

- Never rely on tab name == job name; resolve `.query` before putting a job name in an issue.
- Never draft an issue from a FLAKY tab without the user asking — the ≥3-consecutive-failures bar is what justifies `kind/failing-test`.
- If a summary entry is STALE/BROKEN or has empty status, report it as "needs manual look" instead of guessing.
- Newly filed issues land in the SIG Node CI board triage flow — see `signode-ci-board-triage.md` for what happens next; mention that connection in the report when relevant.
