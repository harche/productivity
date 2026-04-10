# Per-Proposal RBAC

Every proposal gets its own RBAC — no shared permissions between proposals.
The operator creates and cleans up RBAC resources per proposal lifecycle.

## How It Works

1. **Analysis agent requests permissions.** During analysis, the agent
   returns an `RBACResult` with namespace-scoped and cluster-scoped rules,
   each with a justification explaining why it's needed.

2. **Operator creates execution RBAC.** At Approved phase, before calling
   the execution agent, the operator creates:
   - **Role + RoleBinding** per target namespace (namespace-scoped rules)
   - **ClusterRole + ClusterRoleBinding** (cluster-scoped rules)
   - All bound to the execution sandbox's ServiceAccount

3. **Operator cleans up.** After completion or failure, all created RBAC
   resources are removed.

## RBAC Layers

### Layer 1: Agent Analysis
The analysis agent proposes minimum-privilege rules based on its diagnosis.
Each rule includes `apiGroups`, `resources`, `verbs`, and a `justification`.

### Layer 2: Target Namespace Resolution
Target namespaces come from `spec.targetNamespaces` if set, or are
extracted from the namespace-scoped rules in the RBAC result.
Persisted to annotation `ols.openshift.io/rbac-namespaces` for
cleanup after retry resets status.

### Layer 3: Sandbox Binding
RBAC resources are bound to the execution sandbox's ServiceAccount.
The sandbox SA is read from the SandboxTemplate — the proposal never
chooses its own permissions.

## RBACRule Structure

```yaml
namespaceScoped:
  - namespace: production
    apiGroups: ["apps"]
    resources: ["deployments"]
    resourceNames: ["my-app"]        # optional — narrows to specific resources
    verbs: ["get", "patch"]
    justification: "Scale deployment to fix resource pressure"
clusterScoped:
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list"]
    justification: "Check node capacity"
```

## Naming and Limits

RBAC resource names are derived from the proposal name with a prefix
(`ls-exec-` for namespace-scoped, `ls-exec-cluster-` for cluster-scoped)
and truncated to 63 characters (the DNS label limit).

## Cleanup Resilience

When a retry clears the proposal's Steps, the namespace list for cleanup
is still available via the `ols.openshift.io/rbac-namespaces` annotation.
If the annotation is missing, the operator falls back to reading namespaces
from the selected option's RBAC result.

## Key Principle

The **operator is the policy enforcement point**. The agent proposes
what it needs; the operator decides what to grant. The agent never
has direct access to create its own RBAC.

See also: api/proposal.md (RBACResult fields), developing/reconciler.md
