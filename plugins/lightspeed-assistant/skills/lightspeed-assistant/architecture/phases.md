# Proposal Lifecycle Phases

A LightspeedProposal moves through phases based on its workflow.

## Phase Flow (default — no skips)

```
Pending → Analyzing → Proposed → [user approves] → Approved → Executing → Verifying → Completed
```

## Skip Behavior

**Skip analysis** (`analysis.skip: true`):
Pending → Proposed (auto-approved, no agent analysis)

**Skip execution** (`execution.skip: true`):
Proposed → Approved → AwaitingSync → Verifying → Completed

## AwaitingSync Phase

AwaitingSync is the state entered when execution is skipped (the GitOps
pattern). The operator does not apply changes itself — instead, the
analysis step produces a plan (e.g., a manifest diff or a PR), and the
system waits for the user to apply those changes externally through their
own deployment pipeline. Once the user has applied the changes and is
ready for post-execution validation, they trigger verification by
updating the proposal (e.g., annotating or approving the sync). The
proposal then transitions to Verifying, where the verification agent
confirms the changes took effect. This keeps the operator out of the
apply path while still closing the loop with automated verification.

**Skip verification** (`verification.skip: true`):
Executing → Completed (no post-execution checks)

**Advisory-only** (skip execution + verification):
Analyzing → Proposed → terminal (analysis report only, no action taken)

## User Actions at Proposed Phase

- **Approve** — moves to Approved → Executing
- **Deny** — moves to Denied (terminal)
- **Escalate** — creates child proposal with failure context
- **Chat** — inline steering before decision (modify the plan)

## Failure and Retry

When any phase fails:
1. Failure reason recorded to `status.previousAttempts[]`
2. Step status cleared, attempt counter incremented
3. Proposal returns to Pending for re-analysis with enriched context
4. After `maxAttempts` (default 3), auto-escalates

## Escalation

Creates a child proposal with:
- `spec.parentRef` pointing to parent
- Request text containing original request + all failure history
- Same workflow, owner reference for GC cascade

## Phase Values

`Pending` | `Analyzing` | `Proposed` | `Approved` | `Denied` |
`Executing` | `AwaitingSync` | `Verifying` | `Completed` | `Failed` | `Escalated`

See also: architecture/crd-composition.md, api/proposal.md, examples/advisory.md
