# SIG Node CI Board: Find Reviewers for 'PRs - Needs Reviewer'

For each card in the 'PRs - Needs Reviewer' lane of the SIG Node CI/Test project board (https://github.com/orgs/kubernetes/projects/151, org: kubernetes, project number: 151), decide whether the PR is actually blocked on a reviewer, and if so who is the most suitable person to ask, with a drafted comment that says *why* they were pinged. This is outward-facing: it pages real people. It is strictly recommend-only, and the report must let the user veto or swap any candidate before anything is posted.

## What the Lane Actually Means

Cards land on the board automatically: a project workflow bot adds every PR the day it opens (the filter behaves like `is:pr label:sig/node`, so sig-storage or sig-apps PRs that merely carry `sig/node` leak in) with status Triage. A human then moves the card to 'PRs - Needs Reviewer' on the day they comment `/triage accepted`, and nobody moves it out when a reviewer engages. So the lane means **"triage accepted"**, not "no reviewer". Expect most cards to need re-laning, not a ping; in a live sweep of 27 cards, 15 were re-lanes, 5 re-pings, 7 genuine new asks. The actor and date of these moves are in the REST issue timeline (`added_to_project_v2`, `project_v2_item_status_changed`; status names are not populated there, only actor and date).

## Core Principle

The best reviewer is the person already engaged, then the person who actually reviews that code today, then the person who owns it on paper. OWNERS membership alone is a weak signal: alias lists are long, contain emeritus and dormant people, and Prow's auto-requests are usually ignored. **A review request whose timeline actor is `k8s-ci-robot` or `kubernetes-prow[bot]` counts as zero engagement** (72 of 75 requests in a live sweep were bot-made); check the `review_requested` event actor, not just `reviewRequests[].login`. Every candidate needs at least two independent pieces of evidence, one of which must show they are currently active.

## Data Path: REST First

`gh project item-list` and `gh pr view` burn GraphQL points, and the GraphQL budget is shared with every other session on the machine. Before starting, check the GraphQL resource specifically, since `gh api rate_limit` can show 5000 core remaining while GraphQL is at 22:
`gh api graphql -f query='{ rateLimit { remaining resetAt } }'`

- **Board listing:** one lean GraphQL query per page, about 1 point per 100 items (14 pages for ~1300 cards). Select only `id`, the Status field value, and `content { number, repository { nameWithOwner } }`. Cache the result to a file and reuse it for the session.
- **Everything else via REST** (`gh api repos/<R>/...`): `pulls/<N>` (head sha, labels, mergeable state, `html_url`), `pulls/<N>/reviews`, `issues/<N>/comments`, `pulls/<N>/comments` (review threads, needed for `/hold` and the latest exchange), `pulls/<N>/files`, `issues/<N>/timeline` (request actors, label events, project moves), `commits/<SHA>/status`.
- **Search** is 30 requests per minute. Skip liveness lookups for anyone who already appears in the 6-month directory tally (the tally proves liveness) and batch the rest.

## Workflow

1. **List the lane** from the cached board, selecting `Status == "PRs - Needs Reviewer"`. Keep the card `id` (`PVTI_...`), PR number, and repo.

2. **Gate: is the PR really reviewer-blocked?** Run these checks first and stop for any card that fails one; no candidate search for it:
   - (a) `lifecycle/stale`, `lifecycle/rotten`, or `needs-rebase` labels → **RE-LANE** to 'PRs Waiting on Author'.
   - (b) `do-not-merge/hold` and who set it: grep issue and review comments for `/hold` plus the `labeled` timeline event. Hold by the author → **BLOCKED**; hold by a reviewer with a stated condition → RE-LANE Waiting on Author, or RE-PING that reviewer if the condition looks met.
   - (c) `commits/<HEAD_SHA>/status` with non-success contexts (red or pending required jobs) → RE-LANE Waiting on Author.
   - (d) "Fixes", "blocked by", "depends on #N" in body or comments: check whether #N merged. Still open → **BLOCKED**.
   - (e) A merged PR with the same title keywords (`gh search prs --repo <R> --merged "<title keywords>"`): if it covers the same change → **SUPERSEDED**, recommend closing this PR with a pointer to the merged one.
   - (f) `lgtm` label absent but an APPROVED or lgtm review exists: the lgtm was dropped by a later push. That is a re-lgtm **RE-PING** to the original reviewer, not a new reviewer.
   - (g) Latest human exchange: if the last review or comment is from a reviewer and the author has not replied → RE-LANE Waiting on Author. If the author replied last and a reviewer went quiet → RE-PING that reviewer.
   - Draft PRs → RE-LANE Waiting on Author.

3. **Gather candidate signals** for cards that pass the gate (each contributes an evidence line):
   - **Engaged already.** Anyone who reviewed or commented substantively, or issued `/triage accepted`, `/ok-to-test`, `/assign`, or a human `/cc`. Ignore `k8s-ci-robot`, `kubernetes-prow`, `github-project-automation`. First choice: ask them to finish or hand off.
   - **Human review requests.** From the timeline, `review_requested` events whose actor is a person. Bot requests are noise. A human-requested reviewer silent for 30+ days counts *against* themselves; list them but do not re-pick without saying they were already asked.
   - **OWNERS for touched paths.** For each file, walk up to the nearest `OWNERS` (`gh api repos/<R>/contents/<dir>/OWNERS -H 'Accept: application/vnd.github.raw'`), expand aliases from the repo root `OWNERS_ALIASES`, drop `emeritus_*`. Approvers outrank reviewers because the PR will need an approver eventually. For kubernetes/test-infra node jobs the file is `config/jobs/kubernetes/sig-node/OWNERS`.
   - **Active reviewers of that directory (strongest signal).** Build it via REST without Search or GraphQL: `repos/<R>/commits?path=<DIR>&since=<6 months ago>` → `commits/<SHA>/pulls` to map to merged PRs → `pulls/<N>/reviews` plus issue comments containing `/lgtm` or `/approve`. Count distinct PRs per person, drop the PR author and bots (`k8s-ci-robot` appears as a "reviewer" via its auto comments). Sample for `test/e2e_node` over 36 merged PRs: SergeyKanzhelev 11, ffromani 10, haircommander 7, dims 7, pohly 5, HirazawaUi 4.
   - **Git history of touched files.** `repos/<R>/commits?path=<file>&per_page=30`, group by author login. Marks domain knowledge; not review rights.
   - **KEP authors (when the PR is KEP-related).** Link the PR to a KEP, in order of confidence:
     1. Explicit: `KEP-NNNN`, a `kep.k8s.io/NNNN` link, or a kubernetes/enhancements issue number in the title, body, or release-note block.
     2. Feature gate in the diff: any `features.<Gate>` symbol in changed files. Map the gate to a KEP by searching `keps/sig-node/*/kep.yaml` (newer KEPs list `feature-gates:`) and `README.md` for the gate name. Mark as inferred.
     3. Directory or test-name keyword (swap, cgroup, dra, userns, sidecar, hugepages) matched against `keps/sig-node/NNNN-<slug>` directory names (`gh api repos/kubernetes/enhancements/contents/keps/sig-node --jq '.[] | select(.type=="dir") | .name'`). Lowest confidence; say so.
     Then read `gh api repos/kubernetes/enhancements/contents/keps/sig-node/<dir>/kep.yaml -H 'Accept: application/vnd.github.raw'` for `authors`, `reviewers`, `approvers`, `status`, `stage`, and check who touched the KEP recently (`repos/kubernetes/enhancements/commits?path=keps/sig-node/<dir>&per_page=20`). KEP authors with a recent KEP commit rank high; a KEP author with no org activity is stale. KEP authors cannot necessarily `/lgtm`, so pair one with an OWNERS approver rather than making them the sole ask.
   - **Topic hints.** Title, labels, and job names map to known area people: DRA and device plugins to the `keps/sig-node/*dra*` authors and `test/e2e/dra/OWNERS`; CRI-O, conmon, and crun to `config/jobs/kubernetes/sig-node/OWNERS` cri-o entries; swap, cgroups, and resource management to the matching KEP authors. Tie-breaker only.

4. **Filter and rank.**
   - **Exclude:** the PR author, emeritus entries, anyone who explicitly declined on the PR, and anyone with no org activity in 60 days. Liveness for people outside the directory tally: `search/issues?q=org:kubernetes+involves:<LOGIN>+updated:>=<60 days ago>` (one call each, mind the 30/minute cap).
   - **Load, ranked relative to peers.** `search/issues?q=org:kubernetes+is:pr+is:open+review-requested:<LOGIN>`. Absolute cutoffs do not work in this org (live sample: dims 121, bart0sh 61, ffromani 52, SergeyKanzhelev 51 and already on 11 of 27 lane cards). Compare within the same tally, and **always offer a lighter alternative next to the obvious heavy hitter**.
   - **Rank** by: engaged already > active reviewer of the directory (tally) > OWNERS approver > KEP author with recent KEP activity > OWNERS reviewer > git-history author > topic hint. Present the top 2 or 3 per PR with their evidence lines; never show a bare score.

5. **Verdict per card**, one of:
   - **RE-LANE** — not reviewer-blocked (gate failed) or someone is already reviewing. Print the `gh project item-edit` command to the right lane (IDs per board-triage.md / board-todo-sweep.md) and no ping.
   - **RE-PING** — an engaged reviewer stalled, or an lgtm needs refreshing. Draft a short comment addressed to them.
   - **NEW ASK** — draft a `/cc` comment naming 1 to 2 candidates with the reason for each. `/cc @login` is a Prow request-review; use `/assign @login` only if the user prefers assignment.
   - **SUPERSEDED** — an equivalent PR already merged. Draft a closing comment pointing at it and recommend moving the card to 'Archive-it' (never 'Done', see board-todo-sweep.md).
   - **BLOCKED** — dependency PR open or author hold. No ping; note what it waits on and leave the card, or RE-LANE to Waiting on Author if the hold is the author's.

6. **Draft the comment** so the reason is explicit and checkable, for example:
   `gh pr comment <NUM> --repo <REPO> --body $'/cc @kannon92\n@kannon92 pinging you because you reviewed three of the last merged PRs in test/e2e_node and co-authored KEP-2400; this one has been waiting for a reviewer since June. Happy to find someone else if you are swamped.'`
   Keep it to one reason per person, name the KEP or directory, and give an out.

7. **Report.** Every printed card line carries the PR `html_url`. Per PR: candidate, evidence (engaged / dir-reviewer tally / OWNERS role / KEP role / last activity / open requests relative to peers), verdict, then a copy-pasteable block of the drafted commands. End with a tally ("15 re-lane, 5 re-ping, 5 new ask, 1 superseded, 1 blocked") and a reminder that nothing was posted.

## Quality Control

- **Never post a comment or change a card without explicit user approval.** Pinging a person is the outward-facing action here; the user knows about PTO, release crunch, and who volunteered at the CI meeting, which `gh` cannot see.
- Two signals minimum per candidate, one of them liveness. A name that appears only in an OWNERS alias, or only as a bot-made review request, is not a candidate.
- Prefer re-laning over pinging when the gate says the PR is not actually blocked on a reviewer.
- Check the GraphQL rate limit before the board query, and cache the board to a file. Keep Search under 30 calls per minute.
- Scripts must be zsh-safe on macOS: unquoted `$var` does not word-split in zsh, so `for spec in "repo path n"; do ./tally.sh $spec` passes one argument. Use `bash -c`, `set -- $spec` under `setopt shwordsplit`, or explicit arrays.
- If OWNERS, aliases, or the KEP layout differ from what is described here, adapt to the real files rather than assuming.
- Never use `gh project item-delete`; lane changes are Status edits only.
