---
description: Draft a GitHub pending review for a PR, in chat first, with code links as evidence
argument-hint: "[this pr | PR-URL-or-number] [focus]"
---

# Review

REQUEST: $ARGUMENTS

Draft a pending GitHub review. Show the full draft in chat first. Post
nothing until the user says to post. Never submit the review.

## 1. Resolve and gather

- Resolve the PR as `/devkit:explain` section 1 does. Text after the PR
  reference is the **focus** (for example "error handling", "the restore
  path"). Stay inside the focus if one is given.
- Gather context as `/devkit:explain` sections 2–3 do, plus:
  - `headRefOid`: all links and comments pin to this SHA.
  - Existing review threads, resolved or not: do not repeat a point that
    someone already made. If you agree with it, add to that thread.
  - Your own pending review:
    `gh api repos/{owner}/{repo}/pulls/<N>/reviews --jq '.[] | select(.state=="PENDING") | .id'`.
    GitHub allows only one pending review per user. If one exists, say so
    in the draft and ask: add to it, or replace it.

## 2. Review

- Read the changed code at the head SHA, plus the callers and tests that
  the change affects. Do not review from the diff alone.
- Check each point before you draft it: show it with the code, a test, or
  a concrete input. Drop points you cannot back up, or turn them into a
  question.
- Prefer few strong comments over many weak ones. Leave out style nits
  unless the repo's linters or contributor guide require them.

## 3. Draft (in chat)

**Review body**: 1–2 sentences at most, or empty. Do not repeat or
describe the PR. Only what does not fit an inline comment (an overall
concern, or a question about the approach).

**Inline comments**, one block each:

```
### path/to/file.go:L120-L128 (RIGHT)
<comment text exactly as it will be posted>
```

Comment rules:

- Friendly, informal, concise. No emojis. No praise padding, no "Great
  PR!". Ask when unsure ("Is this meant to…?"), say it plainly when sure.
- Back up a claim with a GitHub permalink on its own line, pinned to the
  head SHA, so GitHub renders the snippet:
  `https://github.com/{owner}/{repo}/blob/<headSHA>/<path>#L<a>-L<b>`.
  Code outside the diff (callers, tests, other packages) can be linked
  the same way.
- Use a ```` ```suggestion ```` block for a small concrete fix on the
  commented lines.
- Each inline comment must anchor to a line in the diff. GitHub rejects
  anything else, so a point about code outside the diff goes in the body
  or on the nearest changed line, with a permalink.

End the draft with: `N inline comments, body: <empty | 1 line>. Say "post"
to create the pending review.` Then stop and wait.

## 4. Iterate

Apply the user's edits to the draft and show only the changed blocks.
Repeat until they say "post".

## 5. Post (only after an explicit "post")

Create the review **without** an `event`, so it stays PENDING:

```bash
gh api repos/{owner}/{repo}/pulls/<N>/reviews -X POST --input review.json
```

```json
{
  "commit_id": "<headSHA>",
  "body": "<body>",
  "comments": [
    {"path": "<path>", "line": 128, "start_line": 120, "side": "RIGHT", "body": "<comment>"}
  ]
}
```

- Leave out `start_line` for single-line comments.
- Adding to an existing pending review: use GraphQL
  `addPullRequestReviewThread` with that review's node ID.
- On a 422 (line not in the diff, stale SHA): fix the anchor, show the
  change, and ask again. Do not move comments silently.
- Never send `event` (`COMMENT`, `APPROVE`, `REQUEST_CHANGES`). The
  user submits the review in the GitHub UI.

Report the review URL and the number of comments posted.
