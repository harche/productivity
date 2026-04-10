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
`startedAt`, `completedAt`, `conditions`, `sandbox` (SandboxInfo).

#### AnalysisStepStatus

Common step fields plus:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `options` | []RemediationOption | no | Remediation options returned by the analysis agent |
| `selectedOption` | *int | no | 0-based index of the user-approved option. Used by the operator to determine which option's RBAC to apply during execution. |
| `components` | []JSON | no | Optional adapter-specific UI components |

#### ExecutionStepStatus

Common step fields plus:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | *bool | no | Whether execution completed successfully |
| `actionsTaken` | []ExecutionAction | no | List of actions the agent performed |
| `verification` | *ExecutionVerification | no | Inline verification from the execution agent |
| `components` | []JSON | no | Optional adapter-defined structured data |

#### VerificationStepStatus

Common step fields plus:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | *bool | no | Whether verification passed |
| `checks` | []VerifyCheck | no | Individual verification check results |
| `summary` | string | no | Human-readable verification summary |
| `components` | []JSON | no | Optional adapter-defined structured data |

### Key Nested Types

#### RemediationOption

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Short human-readable name (e.g., "Update image", "Add security context") |
| `summary` | string | no | One-line summary for collapsed views |
| `diagnosis` | DiagnosisResult | yes | Root cause analysis for this option |
| `proposal` | ProposalResult | yes | Remediation plan |
| `verification` | *VerificationPlan | no | Verification plan |
| `rbac` | *RBACResult | no | RBAC permissions needed for execution |
| `components` | []JSON | no | Adapter-defined structured data. Each entry must be a valid JSON object with at least a "type" field. |

#### DiagnosisResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `summary` | string | yes | Human-readable diagnosis summary |
| `confidence` | string | yes | Agent's confidence level. Enum: `low`, `medium`, `high` |
| `rootCause` | string | yes | One-line root cause description |

#### ProposalResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | yes | Human-readable description of the remediation |
| `actions` | []ProposedAction | yes | List of proposed actions |
| `risk` | string | yes | Assessed risk level. Enum: `low`, `medium`, `high`, `critical` |
| `reversible` | bool | yes | Whether the remediation can be rolled back |
| `estimatedImpact` | string | no | Expected impact description |

#### ProposedAction

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | Action type (e.g., patch, scale, restart) |
| `description` | string | yes | Human-readable description of the action |

#### VerificationPlan

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | yes | Human-readable description |
| `steps` | []VerificationStep | no | List of verification steps |
| `rollbackPlan` | RollbackPlan | no | How to roll back the remediation |

#### VerificationStep

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Check name |
| `command` | string | yes | Command to run |
| `expected` | string | yes | Expected result |
| `type` | string | yes | Check type |

#### RollbackPlan

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | yes | Human-readable description |
| `command` | string | yes | Rollback command |

#### RBACResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespaceScoped` | []RBACRule | no | Rules applied via Role in target namespaces |
| `clusterScoped` | []RBACRule | no | Rules applied via ClusterRole |

#### RBACRule

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | no | Target namespace (namespace-scoped rules only) |
| `apiGroups` | []string | yes | API groups |
| `resources` | []string | yes | Resources |
| `resourceNames` | []string | no | Specific named resources |
| `verbs` | []string | yes | Allowed verbs |
| `justification` | string | yes | Why this permission is needed |

#### ExecutionAction

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | Action type |
| `description` | string | yes | What was done |
| `success` | bool | yes | Whether this action succeeded |
| `output` | string | no | Action output |
| `error` | string | no | Error message if the action failed |

#### ExecutionVerification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conditionImproved` | bool | yes | Whether the condition improved |
| `summary` | string | yes | Human-readable summary |

#### VerifyCheck

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Check name |
| `source` | string | yes | Where the check ran (e.g., "oc get pods") |
| `value` | string | yes | Observed value |
| `passed` | bool | yes | Whether the check passed |

#### SandboxInfo

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claimName` | string | no | Name of the SandboxClaim |
| `namespace` | string | no | Namespace of the SandboxClaim |
| `startedAt` | Time | no | When the sandbox was created |
| `completedAt` | Time | no | When the sandbox finished |

#### PreviousAttempt

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `attempt` | int | yes | Attempt number (1-based) |
| `failedPhase` | SandboxPhase | no | Phase where the failure occurred (analysis/execution/verification) |
| `failureReason` | string | no | Error message from the failed phase |

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
