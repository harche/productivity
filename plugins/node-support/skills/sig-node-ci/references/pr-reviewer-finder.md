# SIG Node CI Board: Find Reviewers for 'PRs - Needs Reviewer'

For each card in the 'PRs - Needs Reviewer' lane of the SIG Node CI/Test project board (https://github.com/orgs/kubernetes/projects/151, org: kubernetes, project number: 151), work out who is the most suitable person to ask for a review, and draft a comment that says *why* they were pinged. This is outward-facing: it pages real people. It is strictly recommend-only, and the report must let the user veto or swap any candidate before anything is posted.

## Core Principle

The best reviewer is the person already engaged, then the person who actually reviews that code today, then the person who owns it on paper. OWNERS membership alone is a weak signal: alias lists are long, contain emeritus and dormant people, and Prow's auto-requests are often ignored. Every candidate needs at least two independent pieces of evidence, one of which must show they are currently active.

## Workflow

1. **List the lane.** `gh project item-list 151 --owner kubernetes --format json --limit 500`, select `.status == "PRs - Needs Reviewer"`. Each item gives `content.number`, `content.repository`, and the card `id` (`PVTI_...`).
2. **Pull the PR.** `gh pr view <NUM> --repo <REPO> --json author,title,body,files,labels,reviewRequests,reviews,assignees,comments,updatedAt,isDraft,mergeable`. Capture:
   - touched paths (`files[].path`)
   - who is already requested (`reviewRequests[].login`) and since when (`gh api repos/<REPO>/issues/<NUM>/timeline --paginate --jq '[.[] | select(.event=="review_requested") | {who:.requested_reviewer.login, at:.created_at}]'`)
   - who has engaged: `reviews[].author.login`, human `comments[]` (ignore `k8s-ci-robot`, `kubernetes-prow`), and anyone who issued `/triage accepted`, `/ok-to-test`, `/assign`, or `/cc`
   - PR state: draft, failing CI, needs rebase, or waiting on author. If the author has not addressed an existing review, the card belongs in 'PRs Waiting on Author', not here. Say so and stop for that card.
3. **Gather candidate signals** (run all; each contributes an evidence line):
   - **Engaged already.** Anyone from step 2 who reviewed or commented substantively. First choice: ask them to finish or hand off.
   - **Prow request status.** Requested reviewers who have responded are engaged. Requested reviewers silent for 30+ days count *against* themselves; list them but do not re-pick them without saying they were already asked.
   - **OWNERS for touched paths.** For each file, walk up to the nearest `OWNERS` (`gh api repos/<REPO>/contents/<dir>/OWNERS -H 'Accept: application/vnd.github.raw'`), expand aliases from the repo root `OWNERS_ALIASES`, drop `emeritus_approvers`/`emeritus_reviewers`. Approvers outrank reviewers because the PR will need an approver eventually. For kubernetes/test-infra node jobs the relevant file is `config/jobs/kubernetes/sig-node/OWNERS`.
   - **Active reviewers of that directory.** `gh search prs --repo <REPO> --merged --limit 30 "<dir>"`, then for each result `gh pr view <N> --json reviews --jq '.reviews[] | select(.state=="APPROVED" or .state=="COMMENTED") | .author.login'`; tally. This is the strongest "active and willing" signal. Restrict to the last 6 to 12 months (`--merged-at ">=<date>"`).
   - **Git history of touched files.** `gh api 'repos/<REPO>/commits?path=<file>&per_page=30' --jq '[.[] | .author.login] | group_by(.) | map({who:.[0], n:length}) | sort_by(-.n)'`. Marks domain knowledge; not review rights.
   - **KEP authors (when the PR is KEP-related).** Link the PR to a KEP, in order of confidence:
     1. Explicit: `KEP-NNNN`, a `kep.k8s.io/NNNN` link, or a kubernetes/enhancements issue number in the title, body, or release-note block.
     2. Feature gate in the diff: any `features.<Gate>` symbol in changed files. Map the gate to a KEP by searching `keps/sig-node/*/kep.yaml` (newer KEPs list `feature-gates:`) and `README.md` for the gate name. Mark as inferred.
     3. Directory or test-name keyword (swap, cgroup, dra, userns, sidecar, hugepages) matched against `keps/sig-node/NNNN-<slug>` directory names (`gh api repos/kubernetes/enhancements/contents/keps/sig-node --jq '.[] | select(.type=="dir") | .name'`). Lowest confidence; say so.
     Then read `gh api repos/kubernetes/enhancements/contents/keps/sig-node/<dir>/kep.yaml -H 'Accept: application/vnd.github.raw'` for `authors`, `reviewers`, `approvers`, `status`, `stage`, and check who touched the KEP recently (`gh api 'repos/kubernetes/enhancements/commits?path=keps/sig-node/<dir>&per_page=20'`). KEP authors with a recent KEP commit rank high; a KEP author with no org activity is stale. KEP authors cannot necessarily `/lgtm`, so pair one with an OWNERS approver rather than making them the sole ask.
   - **Topic hints.** Title, labels, and job names map to known area people: DRA and device plugins to the `keps/sig-node/*dra*` authors and `test/e2e/dra/OWNERS`; CRI-O, conmon, and crun to `config/jobs/kubernetes/sig-node/OWNERS` cri-o entries; swap, cgroups, and resource management to the matching KEP authors. Treat as a tie-breaker, not evidence on its own.
4. **Filter and rank.**
   - **Exclude:** the PR author, emeritus entries, anyone who explicitly declined on the PR, and anyone with no comment/review/commit in the kubernetes org in the last 60 days (`gh search issues --commenter <LOGIN> --updated ">=<date>" --limit 1` plus `gh search prs --reviewed-by <LOGIN> --updated ">=<date>" --limit 1`).
   - **Load check:** `gh search prs --repo <REPO> --state open --review-requested <LOGIN> --json number --jq length`. Flag anyone above roughly 15 open requests; prefer someone lighter if the evidence is otherwise close.
   - **Rank** by: engaged already > active reviewer of the directory (tally) > OWNERS approver > KEP author with recent KEP activity > OWNERS reviewer > git-history author > topic hint. Present the top 2 or 3 per PR with their evidence lines; never show a bare score.
5. **Verdict per card**, one of:
   - **RE-LANE** — someone is already reviewing, or the PR is waiting on the author / draft / red CI. Print the `gh project item-edit` command to move it to the right lane (see board-triage.md for ID resolution) and no ping.
   - **RE-PING** — a requested reviewer is engaged but stalled. Draft a short comment addressed to them.
   - **NEW ASK** — draft a `/cc` comment naming 1 to 2 candidates with the reason for each. `/cc @login` is a Prow request-review; use `/assign @login` only if the user prefers assignment.
6. **Draft the comment** so the reason is explicit and checkable, for example:
   `gh pr comment <NUM> --repo <REPO> --body $'/cc @kannon92\n@kannon92 pinging you because you reviewed three of the last merged PRs in test/e2e_node and co-authored KEP-2400; this one has been waiting for a reviewer since June. Happy to find someone else if you are swamped.'`
   Keep it to one reason per person, name the KEP or directory, and give an out.
7. **Report** a table per PR: candidate, evidence (engaged / dir-reviewer tally / OWNERS role / KEP role / last activity / open requests), verdict, then a copy-pasteable block of the drafted commands. End with a tally ("2 re-lane, 1 re-ping, 1 new ask") and a reminder that nothing was posted.

## Quality Control

- **Never post a comment or change a card without explicit user approval.** Pinging a person is the outward-facing action here; the user knows about PTO, release crunch, and who volunteered at the CI meeting, which `gh` cannot see.
- Two signals minimum per candidate, one of them liveness. A name that appears only in an OWNERS alias is not a candidate.
- Prefer re-laning over pinging when the evidence says the PR is not actually blocked on a reviewer.
- If OWNERS, aliases, or the KEP layout differ from what is described here, adapt to the real files rather than assuming.
- Never use `gh project item-delete`; lane changes are Status edits only.
