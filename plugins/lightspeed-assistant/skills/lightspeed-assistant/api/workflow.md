# OlsWorkflow

Cluster-scoped. Defines a reusable 3-step pipeline template: which agent
handles analysis, execution, and verification.

**Source:** `lightspeed-operator/api/v1alpha1/workflow_types.go`

## Spec Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `analysis` | WorkflowStep | yes | Analysis step config |
| `execution` | WorkflowStep | yes | Execution step config |
| `verification` | WorkflowStep | yes | Verification step config |

### WorkflowStep

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent` | string | when not skipped | Name of an OlsAgent CR |
| `skip` | bool | no | Skip this step entirely (default: false) |

## CEL Validation

Agent is required when skip is false. The CRD enforces this:
- `analysis.agent` required when `analysis.skip` is false
- Same for execution and verification

## Skip Patterns

| Pattern | Analysis | Execution | Verification | Use Case |
|---------|----------|-----------|--------------|----------|
| Full remediation | agent | agent | agent | Auto-fix with verification |
| Advisory-only | agent | skip | skip | Analysis report, no action |
| GitOps | agent | skip | agent | User applies fix, agent verifies |
| Trust mode | skip | agent | agent | Execute immediately, verify |

## Example

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: remediation
spec:
  analysis:
    agent: analyzer
  execution:
    agent: executor
  verification:
    agent: verifier
```

## kubectl Columns

```
NAME           ANALYSIS AGENT   EXEC SKIP   VERIFY SKIP   AGE
remediation    analyzer         false        false         1d
advisory-only  analyzer         true         true          1d
```

See also: api/agent.md, api/proposal.md (references workflow), architecture/phases.md (skip behavior)
