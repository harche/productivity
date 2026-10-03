---
description: Explain a GitHub PR or issue from its full context, in ASD-STE100
argument-hint: "[this pr | this issue | PR-or-issue-URL-or-number]"
---

# Explain

REQUEST: $ARGUMENTS

Explain a PR or an issue. The "why" comes from the people who wrote,
reported and reviewed it, not from guessing.

## 1. Resolve the target

**Explicit reference** (parse like `/devkit:worktree`):

- `https://github.com/owner/repo/pull/123` → PR 123
- `https://github.com/owner/repo/issues/123` → issue 123
- `pr-123`, `pr 123`, `pull 123` (slug suffix allowed) → PR 123
- `issue-123`, `issue 123` (slug suffix allowed) → issue 123
- Bare `123` / `#123`: try `gh pr view 123`, fall back to `gh issue view 123`.

**Implicit reference** (`this pr`, `this issue`, `this`, `current`, or
empty REQUEST): infer it from the current context, first match wins:

1. The PR or issue already discussed in this conversation.
2. Branch name: `git branch --show-current` matches `pr-<N>[-slug]` or
   `issue-<N>[-slug]`.
3. Worktree path: `git rev-parse --show-toplevel` ends in
   `.worktrees/pr-<N>[-slug]` or `.worktrees/issue-<N>[-slug]`.
4. Upstream PR for the branch: `gh pr view --json number,url`.

Match the kind that was asked for:

- `this issue` while on a PR: use the PR's `closingIssuesReferences`. If
  there are none, look for `#N` issue references in the PR body. If there
  are several, list them and ask.
- `this pr` while on an issue: use the open PRs that the issue timeline
  links. If there are several, list them and ask.

State the resolved target in the first line of the output, for example
`PR #142124 (from worktree pr-142124)`. If nothing resolves, ask. Never
explain a bare local diff as if it were the PR.

## 2. Gather context FIRST

Run in parallel.

**PR:**

```bash
gh pr view <N> --json title,body,author,state,labels,commits,reviewDecision,closingIssuesReferences,url
gh pr view <N> --comments
gh api repos/{owner}/{repo}/pulls/<N>/comments --paginate --jq '.[] | "\(.user.login) \(.path):\(.line): \(.body)"'
gh pr checks <N>
```

**Issue:**

```bash
gh issue view <N> --json title,body,author,state,stateReason,labels,assignees,milestone,url
gh issue view <N> --comments
gh api repos/{owner}/{repo}/issues/<N>/timeline --paginate \
  --jq '.[] | select(.event=="cross-referenced" or .event=="connected" or .event=="closed") | {event, by: .actor.login, src: .source.issue.html_url, title: .source.issue.title, state: .source.issue.state}'
```

**Both:** follow the references:

- `#123` and PR/issue URLs in the body, commits or comments: read title + body.
- `discussion_r<ID>` links: `gh api repos/{owner}/{repo}/pulls/comments/<ID>`,
  plus its replies (`in_reply_to_id == <ID>` on that PR's review comments).
- For an issue, linked or closing PRs: title, state, short diff summary.
- KEPs and design docs: read the relevant section, not the whole document.

Ignore bot boilerplate (triage, approval notifier) except for concrete
state: missing approvals, failing checks, `lifecycle/stale`.

## 3. Read the code

- **PR:** `gh pr diff <N>` (or `git diff <base>...HEAD` in the worktree).
  This gives the "what". If the diff does not match the description, say so.
- **Issue:** read the files, functions, logs or tests that the issue names.
  Check the claims you can check (does the code path exist, does it still
  look like that on the default branch). Do not attempt a fix.

## 4. Write the explanation

**PR sections:**

1. **Title / type**: title, kind label, user-facing or not, release note.
2. **Background**: who asked for it and where (link), linked issues.
3. **Problem**: the motivation in the author's/reviewers' terms.
4. **Changes**: numbered list grounded in the diff, with function, file
   and field names.
5. **Result**: what is now true. Repeat explicit claims such as "no
   functional change" only after checking them against the diff.
6. **Status**: approvals needed, failing checks (related to the diff or
   probably a flake), open review threads.

**Issue sections:**

1. **Title / type**: title, kind/sig/priority labels, state (+ reason).
2. **Report**: what the reporter saw, the environment, the version.
3. **Problem**: the cause, if known or agreed; else "not yet known".
4. **Evidence**: reproduction steps, logs, the code you checked.
5. **Discussion**: proposals, decisions, disagreements, with who said each.
6. **Linked work**: PRs and their state, related or duplicate issues.
7. **Status**: triage state, assignee, what blocks progress.

**Rules:**

- Never invent motivation or a cause. If the sources do not give one,
  write that, then give your inference, labeled as inference.
- Cite sources for claims about intent (body, comment link, reviewer).
- Keep code identifiers exactly as written, in backticks.

### Language: ASD-STE100

Write all output in ASD-STE100 Simplified Technical English.

- One topic per sentence. Max 20 words for procedural sentences, max 25
  for descriptive sentences. Max 6 sentences per paragraph.
- Active voice. Simple tenses: present, past, future.
- Use the STE approved meaning of words ("make", "change", "use", "show").
  One word for one concept; do not use synonyms for variety.
- Use articles ("the", "a") where English permits.
- Technical names and code identifiers are allowed as they are.
- Use numbered lists for sequences and bullets for sets of items.
- No idioms, no phrasal verbs where a single verb exists, no "-ing" nouns
  when a verb works.

## 5. Report

Give the explanation in chat. End with one line listing the sources you read
(body, N comments, N review threads, linked PRs/issues, checks) so gaps
are visible.
