# Reconciler Internals

The proposal reconciler is a phase-driven state machine.
Each phase has a handler that transitions to the next phase.

**File:** `internal/controller/proposal/reconciler.go`

## Phase Handlers

| Phase | Handler | What It Does |
|-------|---------|--------------|
| Pending | `handlePending` | Calls analysis agent, parses response, transitions to Proposed |
| Approved | `handleApproved` | Creates execution RBAC, calls execution agent, transitions to Verifying |
| Verifying | `handleVerifying` | Calls verification agent, transitions to Completed or Failed |
| AwaitingSync | `handleAwaitingSync` | Waits for external trigger to start verification |
| Failed | `handleFailed` | Records failure, retries or escalates |
| Escalated | `handleEscalated` | Creates child proposal with failure history |

Phases without handlers (Proposed, Denied, Completed) are terminal
or waiting for user action (approve/deny via console or API patch).

## callAgent Flow

```
callAgent(ctx, proposal, phase, step, query)
  ├── ensureAgentTemplate → SandboxTemplate name
  ├── sandbox.Claim → SandboxClaim name
  ├── setClaimOwnerReference (GC on proposal delete)
  ├── Track sandbox info on step status
  ├── sandbox.WaitReady (5-min timeout) → endpoint
  ├── readSystemPrompt (from ConfigMap)
  ├── buildContext (targetNamespaces, attempt, previousAttempts)
  ├── Select output schema per phase
  └── lsClient.Call(endpoint, prompt, query, schema, context) → response
```

## Workflow Resolution

**File:** `internal/controller/proposal/resolve.go`

1. Fetch OlsWorkflow CR by `proposal.Spec.Workflow` name
2. Extract steps (analysis, execution, verification)
3. Apply `proposal.Spec.WorkflowOverride` (merge skip/agent overrides)
4. For each non-skipped step: fetch OlsAgent CR → fetch OlsLlmProvider CR
5. Return `resolvedWorkflow` with all steps fully resolved or marked Skip

## Retry Logic

- Failed phase records to `status.previousAttempts[]`
- Step status cleared, attempt counter incremented
- Proposal returns to Pending for re-analysis
- Previous failure context is included in the next agent query
- After `maxAttempts` (default 3), transitions to Escalated

## Escalation

- Creates child proposal with `spec.parentRef` = parent name
- Child request = original request + formatted failure history
- Owner reference set for GC cascade
- Parent stops reconciling after escalation

## RBAC Flow

**File:** `internal/controller/proposal/rbac.go`

At Approved phase, before execution:
1. Read `status.steps.analysis.rbac` (what the agent requested)
2. Determine target namespaces (spec or extracted from rules)
3. Create Role+RoleBinding per namespace, ClusterRole+ClusterRoleBinding
4. Bind to execution sandbox ServiceAccount
5. Clean up after completion/failure

See also: architecture/rbac.md, architecture/phases.md
