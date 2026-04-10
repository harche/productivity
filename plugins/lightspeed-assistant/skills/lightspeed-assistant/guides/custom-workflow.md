# Designing Custom Workflows

A workflow wires agents to 3 steps. By choosing which agents to
assign and which steps to skip, you create different behavior patterns.

## The 3 Steps

1. **Analysis** — Diagnose the issue, propose a remediation plan, request RBAC
2. **Execution** — Execute the approved plan with scoped permissions
3. **Verification** — Independently verify the fix worked

## Common Patterns

### Full Remediation
All 3 steps active. Agent analyzes, user approves, agent executes, agent verifies.
```yaml
spec:
  analysis:
    agent: analyzer
  execution:
    agent: executor
  verification:
    agent: verifier
```

### Advisory-Only
Analysis only. No execution, no verification. Good for compliance auditing.
```yaml
spec:
  analysis:
    agent: analyzer
  execution:
    skip: true
  verification:
    skip: true
```

### GitOps Remediation
Agent analyzes and verifies, but skips execution. User applies changes
via GitOps (ArgoCD, Flux), then the proposal enters AwaitingSync
and can be manually triggered to verify.
```yaml
spec:
  analysis:
    agent: analyzer
  execution:
    skip: true
  verification:
    agent: verifier
```

### Trust Mode
Skip analysis — go straight to execution. For well-understood,
pre-approved operations where analysis is unnecessary overhead.
```yaml
spec:
  analysis:
    skip: true
  execution:
    agent: executor
  verification:
    agent: verifier
```

## Per-Proposal Overrides

Override any step for a single proposal without creating a new workflow:

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: LightspeedProposal
metadata:
  name: one-off-advisory
spec:
  request: "Check node CPU pressure"
  workflow: remediation          # normally does full remediation
  workflowOverride:
    execution:
      skip: true                 # but skip execution for this one
    verification:
      skip: true
```

This uses the `remediation` workflow's analyzer but makes it advisory-only.

## maxAttempts — Per-Proposal Retry Limit

Override the global retry limit for a single proposal with `maxAttempts`.
Valid range is 0-20. When a step fails, the operator retries from the
beginning of that step up to this many times before moving to Failed
or Escalated.

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: LightspeedProposal
metadata:
  name: persistent-issue
spec:
  request: "Fix flapping pod in namespace production"
  workflow: remediation
  maxAttempts: 5                  # retry up to 5 times (default is global setting)
  targetNamespaces:
    - production
```

Set `maxAttempts: 0` to disable retries entirely — the proposal fails
on the first error. Use higher values for intermittent issues where
retry is likely to succeed (e.g., transient API errors). The operator
includes `previousAttempts` context in each retry so the agent can
adjust its approach.

## Phase Transitions by Workflow Pattern

Each workflow pattern produces a different sequence of phases. Skipped
steps are not entered — the proposal jumps past them.

### Full Remediation
```
Pending → Analyzing → Proposed → Approved → Executing → Verifying → Completed
                                   ↓                        ↓
                                 Denied                   Failed → Escalated
```

### Advisory-Only (execution + verification skipped)
```
Pending → Analyzing → Proposed
                        ↓
                      Denied
```

### GitOps Remediation (execution skipped, verification active)
```
Pending → Analyzing → Proposed → Approved → AwaitingSync → Verifying → Completed
                                   ↓                                      ↓
                                 Denied                                 Failed → Escalated
```

### Trust Mode (analysis skipped)
```
Pending → Executing → Verifying → Completed
              ↓           ↓
            Failed      Failed → Escalated
```

Any step that fails may trigger a retry (back to the start of that
step) if `maxAttempts` has not been exhausted. After all retries are
spent, the proposal moves to Failed, and if an escalation workflow
is configured, to Escalated.

See also: architecture/phases.md (full phase machine detail)

## Choosing Agents Per Step

Different steps benefit from different model tiers:
- **Analysis:** Use a capable model (e.g., Opus) — needs deep reasoning
- **Execution:** Use a fast model (e.g., Haiku) — follows an approved plan
- **Verification:** Use a capable model — needs independent judgment

See also: api/workflow.md (field reference), architecture/phases.md (skip behavior), examples/
