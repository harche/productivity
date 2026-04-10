# Example: Advisory-Only

Analysis only — diagnose the issue without taking any action.
Good for compliance auditing, investigation, or building confidence
before enabling execution.

## Workflow

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: advisory-only
spec:
  analysis:
    agent: analyzer
  execution:
    skip: true            # no action taken
  verification:
    skip: true            # nothing to verify
```

## Proposal

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: LightspeedProposal
metadata:
  name: investigate-cpu
  namespace: openshift-lightspeed
spec:
  request: "Investigate high CPU usage on node worker-1"
  workflow: advisory-only
  targetNamespaces:
    - default
```

## What Happens

1. **Pending → Analyzing:** Agent investigates using read-only tools
2. **Analyzing → Proposed:** Analysis results shown in console
3. Proposal stays at Proposed — no further action

The analysis still produces a full diagnosis, proposed actions, and
RBAC needs — but since execution is skipped, these are informational.

## Using workflowOverride Instead

You can make any existing workflow advisory-only for a single proposal:

```yaml
spec:
  workflow: remediation         # normally does full remediation
  workflowOverride:
    execution:
      skip: true
    verification:
      skip: true
```

This is useful for one-off investigations using an existing workflow
without creating a new workflow CR.

See also: guides/custom-workflow.md (skip patterns), examples/remediation.md
