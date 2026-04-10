# Example: Standard Remediation

Full 3-phase workflow: analyze the issue, execute the fix, verify it worked.

## Setup

> **Confirm before applying.** Ask the user for confirmation before
> creating any resources on the cluster.

Assumes providers, agents, and workflow from `examples/setup/` are applied.

## Workflow

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: remediation
spec:
  analysis:
    agent: analyzer       # Opus — deep reasoning for diagnosis
  execution:
    agent: executor       # Haiku — follows approved plan quickly
  verification:
    agent: verifier       # Opus — independent judgment on success
```

Three different agents because the steps need different capabilities.
Analysis and verification benefit from a capable model. Execution
follows a pre-approved plan and benefits from speed.

## Proposal

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: LightspeedProposal
metadata:
  name: fix-crashloop
  namespace: openshift-lightspeed
spec:
  request: "Pod frontend-abc is in CrashLoopBackOff in namespace production"
  workflow: remediation
  targetNamespaces:
    - production          # scopes RBAC and agent investigation to this namespace
```

## What Happens

1. **Pending → Analyzing:** Operator calls analyzer agent. Agent investigates
   the cluster, returns diagnosis + proposed actions + RBAC needs.

2. **Analyzing → Proposed:** User sees the plan in the console UI.
   Can approve, deny, escalate, or chat to refine.

3. **Proposed → Approved → Executing:** Operator creates per-proposal RBAC
   (Role+RoleBinding in production namespace), calls executor agent.

4. **Executing → Verifying:** Operator calls verifier agent. Agent
   independently checks if the issue is resolved.

5. **Verifying → Completed:** Fix verified. RBAC cleaned up.

## If It Fails

After failure, the proposal retries (up to `maxAttempts`). Previous
failure context is fed back to the analyzer for a better second attempt.
After max attempts, it escalates to a child proposal.

See also: architecture/phases.md, examples/advisory.md (simpler variant)
