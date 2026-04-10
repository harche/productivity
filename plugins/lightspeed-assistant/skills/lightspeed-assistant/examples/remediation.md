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

## Specialized Remediation Workflows

The standard `remediation` workflow above uses generic agents. Several
adapters define specialized variants with domain-specific agents,
skills images, and system prompts. They follow the same 3-phase
pattern but with tailored analysis.

### AlertManager Remediation

Defined in `examples/setup/06-alertmanager-workflow.yaml`. Used by the
AlertManager adapter when a Prometheus alert fires.

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: alertmanager-remediation
spec:
  analysis:
    agent: alertmanager-analyzer   # alert-aware prompt, Prometheus skills
  execution:
    agent: alertmanager-executor   # AlertManager skills image
  verification:
    agent: alertmanager-verifier   # AlertManager skills image
```

All three agents use the `lightspeed-alertmanager-skills` image, which
includes Prometheus query skills and OpenShift platform docs. The
analysis prompt instructs the agent to query Istio and Prometheus
metrics, check pod logs, and inspect resource limits.

### OSSM (OpenShift Service Mesh) Remediation

Defined in `examples/setup/07-ossm-workflow.yaml`. Used when Istio
sidecar metrics detect service mesh issues (high error rates, latency
spikes, mTLS misconfigurations).

```yaml
# Full remediation: analyze mesh issue -> execute fix -> verify
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: ossm-remediation
spec:
  analysis:
    agent: ossm-analyzer       # understands VirtualService, DestinationRule, etc.
  execution:
    agent: ossm-executor
  verification:
    agent: ossm-verifier
---
# Advisory only: analyze mesh issue, no action
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: ossm-advisory
spec:
  analysis:
    agent: ossm-analyzer
  execution:
    skip: true
  verification:
    skip: true
```

The OSSM analysis prompt teaches the agent to inspect Istio resources
(VirtualService, DestinationRule, PeerAuthentication, AuthorizationPolicy)
and query Istio metrics (`istio_requests_total`, response flags like
UH/UO/NR). Agents use the `lightspeed-alertmanager-skills` image since
OSSM alerts come through the same AlertManager pipeline.

The `ossm-advisory` variant is useful for investigating mesh issues
without making changes -- for example, diagnosing whether a fault
injection rule or circuit breaker is causing errors.

See also: architecture/phases.md, examples/advisory.md (simpler variant), examples/upgrade.md (upgrade workflow)
