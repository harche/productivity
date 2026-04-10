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

## Choosing Agents Per Step

Different steps benefit from different model tiers:
- **Analysis:** Use a capable model (e.g., Opus) — needs deep reasoning
- **Execution:** Use a fast model (e.g., Haiku) — follows an approved plan
- **Verification:** Use a capable model — needs independent judgment

See also: api/workflow.md (field reference), architecture/phases.md (skip behavior), examples/
