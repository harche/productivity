# LightspeedProposal

Namespaced. The actual unit of work. References a workflow, carries the
request, and tracks the full lifecycle through status.

**Source:** `lightspeed-operator/api/v1alpha1/lightspeedproposal_types.go`

## Spec Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request` | string | yes | The original request or trigger description |
| `workflow` | string | yes | Name of an OlsWorkflow CR |
| `targetNamespaces` | []string | no | Namespace(s) this proposal operates on |
| `workflowOverride` | WorkflowOverride | no | Per-proposal step overrides |
| `parentRef` | string | no | Parent proposal name (for escalation chains) |
| `maxAttempts` | int | no | Override global retry limit (0-20) |

### WorkflowOverride

Override any step without creating a new workflow CR:

```yaml
workflowOverride:
  execution:
    skip: true        # make this one advisory-only
  verification:
    agent: my-verifier  # use a different verifier
```

Each step override has optional `skip` (bool) and `agent` (string).

## Status Fields

| Field | Type | Description |
|-------|------|-------------|
| `phase` | ProposalPhase | Current lifecycle phase |
| `attempt` | int | Current attempt number (1-based) |
| `steps` | StepsStatus | Per-step observed state (analysis, execution, verification) |
| `previousAttempts` | []PreviousAttempt | History of failed attempts |
| `conditions` | []Condition | Standard Kubernetes conditions |

### Step Status (per step: analysis, execution, verification)

Each step tracks: `phase` (Pending/Running/Completed/Failed/Skipped),
`startedAt`, `completedAt`, `conditions`, `sandbox` info.

**Analysis-specific:** `diagnosis` (DiagnosisResult), `proposal` (ProposalResult),
`verification` (VerificationPlan), `rbac` (RBACResult)

**Execution-specific:** `success`, `actionsTaken` ([]ExecutionAction),
`verification` (ExecutionVerification)

**Verification-specific:** `success`, `checks` ([]VerifyCheck), `summary`

### Key Nested Types

**DiagnosisResult:** `summary`, `confidence` (low/medium/high), `rootCause`

**ProposalResult:** `description`, `actions` ([]ProposedAction), `risk`
(low/medium/high/critical), `reversible`, `estimatedImpact`

**RBACResult:** `namespaceScoped` ([]RBACRule), `clusterScoped` ([]RBACRule)

**RBACRule:** `namespace`, `apiGroups`, `resources`, `resourceNames`, `verbs`, `justification`

## Example

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
    - production
```

## kubectl Columns

```
NAME            WORKFLOW      PHASE       AGE
fix-crashloop   remediation   Analyzing   30s
```

See also: architecture/phases.md (lifecycle), architecture/rbac.md (RBAC flow), api/workflow.md
