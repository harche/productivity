# Example: Trust Mode

Skip analysis — execute immediately using a pre-defined plan.
Good for well-understood, pre-approved operations where analysis
adds latency without value.

## Workflow

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: trust-mode
spec:
  analysis:
    skip: true            # no analysis — go straight to execution
  execution:
    agent: executor
  verification:
    agent: verifier
```

## Proposal

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: LightspeedProposal
metadata:
  name: restart-flaky-pod
  namespace: openshift-lightspeed
spec:
  request: "Rollout restart deployment/cache-server in namespace production"
  workflow: trust-mode
  targetNamespaces:
    - production
```

## What Happens

1. **Pending → Proposed (auto):** Since analysis is skipped, the proposal
   goes directly to Proposed with no agent call
2. **Proposed → Approved → Executing:** User approves (or auto-approve
   if configured), executor runs the request directly
3. **Executing → Verifying → Completed:** Verifier checks the result

## RBAC Consideration

Without analysis, there's no `RBACResult` from an agent. The executor
operates with whatever RBAC the sandbox ServiceAccount already has.
This means trust-mode proposals need pre-configured RBAC — the operator
won't create per-proposal RBAC without an analysis result.

## When to Use

- Routine operations (restart, scale) where diagnosis is unnecessary
- Runbook-style automation where the action is known in advance
- High-frequency operations where analysis latency is unacceptable

## When NOT to Use

- Unknown or complex issues — analysis catches unexpected factors
- Operations requiring precise RBAC scoping — no agent-requested RBAC
- First-time operations — use full remediation until you trust the pattern

See also: examples/remediation.md (with analysis), guides/custom-workflow.md
