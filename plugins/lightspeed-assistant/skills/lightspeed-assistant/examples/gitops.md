# Example: GitOps Remediation

Agent analyzes and verifies, but execution is skipped. The user
applies changes via GitOps (ArgoCD, Flux, manual git push),
then triggers verification.

## Workflow

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: gitops-remediation
spec:
  analysis:
    agent: analyzer
  execution:
    skip: true            # user applies changes via git
  verification:
    agent: verifier
```

## Proposal

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: LightspeedProposal
metadata:
  name: gitops-fix
  namespace: openshift-lightspeed
spec:
  request: "Resource limits too low on deployment api-server in staging"
  workflow: gitops-remediation
  targetNamespaces:
    - staging
```

## What Happens

1. **Pending → Analyzing → Proposed:** Agent diagnoses and proposes a fix
2. **Proposed → Approved → AwaitingSync:** Since execution is skipped,
   the proposal enters AwaitingSync after approval
3. User applies the recommended changes via git commit + ArgoCD sync
4. User triggers verification (console "Verify Now" or API patch)
5. **AwaitingSync → Verifying → Completed:** Agent verifies the fix

## When to Use

- Namespaces managed by ArgoCD/Flux (direct `oc` writes would be
  reverted by the GitOps controller)
- Teams that require git audit trail for all changes
- Environments where direct cluster writes are policy-prohibited

## Adapter Integration

The AlertManager adapter auto-selects this workflow for ArgoCD-managed
namespaces by checking for the `argocd.argoproj.io/managed-by` annotation.

See also: guides/adapters.md (workflow selection), architecture/phases.md (AwaitingSync)
