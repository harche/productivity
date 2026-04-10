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
Proposed → Approved → AwaitingSync (for GitOps — user applies changes externally, then triggers verification)

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
