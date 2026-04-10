# Example: GitOps Remediation

Agent analyzes and verifies, but execution is skipped. The user
applies changes via GitOps (ArgoCD, Flux, manual git push),
then triggers verification.

## Basic Workflow (from `03-workflows.yaml`)

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

This basic variant uses the standard `analyzer` and `verifier` agents.
It works for general infrastructure issues in GitOps-managed namespaces.

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

1. **Pending -> Analyzing -> Proposed:** Agent diagnoses and proposes a fix
2. **Proposed -> Approved -> AwaitingSync:** Since execution is skipped,
   the proposal enters AwaitingSync after approval
3. User applies the recommended changes via git commit + ArgoCD sync
4. User triggers verification (console "Verify Now" or API patch)
5. **AwaitingSync -> Verifying -> Completed:** Agent verifies the fix

## When to Use

- Namespaces managed by ArgoCD/Flux (direct `oc` writes would be
  reverted by the GitOps controller)
- Teams that require git audit trail for all changes
- Environments where direct cluster writes are policy-prohibited

## Specialized GitOps Workflows

The basic `gitops-remediation` workflow above uses standard agents.
The specialized variants in `examples/setup/08-gitops-workflow.yaml` and
`09-gitops-advisory-workflow.yaml` add GitOps-specific agents with
`gh` CLI access and dedicated system prompts.

### Full GitOps Remediation (automated PR)

```yaml
# Agents with GitHub CLI and GitOps-specific prompts
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: gitops-analyzer
spec:
  llm: smart
  skills:
    image: <registry>/gitops-skills:latest
  systemPromptRef:
    name: gitops-analysis-prompt       # reads git repo, advises YAML changes
---
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: gitops-executor
spec:
  llm: fast
  skills:
    image: <registry>/gitops-skills:latest
  systemPromptRef:
    name: gitops-execution-prompt      # creates + merges PR via `gh`
---
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: gitops-verifier
spec:
  llm: fast
  skills:
    image: <registry>/gitops-skills:latest
  systemPromptRef:
    name: gitops-verification-prompt   # waits for ArgoCD sync, checks cluster

---
# Workflow: analyze → create PR → verify ArgoCD synced the fix
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: gitops-remediation       # same name, replaces basic version
spec:
  analysis:
    agent: gitops-analyzer
  execution:
    agent: gitops-executor       # creates and merges a PR automatically
  verification:
    agent: gitops-verifier
```

Unlike the basic variant, this workflow does NOT skip execution.
The execution agent creates a PR with the fix, merges it, and
ArgoCD syncs the change. The verifier waits for the sync.

### GitOps Advisory (no automated PR)

```yaml
# Advisory agent — reads git repo, advises changes, no PR
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: gitops-advisory-analyzer
spec:
  llm: smart
  skills:
    image: <registry>/gitops-skills:latest
  systemPromptRef:
    name: gitops-advisory-analysis-prompt  # read-only, no git writes

---
# Workflow: analyze → user creates PR manually → verify on demand
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: gitops-advisory-remediation
spec:
  analysis:
    agent: gitops-advisory-analyzer
  execution:
    skip: true                    # user creates the PR themselves
  verification:
    agent: gitops-verifier        # user clicks "Verify Now" after merge
```

Defined in `examples/setup/09-gitops-advisory-workflow.yaml`. The
agent reads the git repo to understand the YAML structure, then
describes the exact changes needed (file paths, diffs). The user
creates and merges the PR manually, then triggers verification.

### GitOps Advisory Only (no verification)

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: gitops-advisory
spec:
  analysis:
    agent: gitops-analyzer
  execution:
    skip: true
  verification:
    skip: true
```

Defined in `examples/setup/08-gitops-workflow.yaml`. Pure analysis --
advises what git changes to make without any follow-up.

## Summary of GitOps Workflow Variants

| Workflow | Execution | Verification | Use Case |
|----------|-----------|--------------|----------|
| `gitops-remediation` (basic) | skip | standard verifier | General GitOps issues |
| `gitops-remediation` (08) | automated PR via `gh` | ArgoCD sync check | Automated end-to-end CVE fix |
| `gitops-advisory-remediation` | skip (user creates PR) | ArgoCD sync check on demand | User-controlled PR workflow |
| `gitops-advisory` | skip | skip | Analysis and advice only |

## Adapter Integration

The AlertManager adapter auto-selects the basic `gitops-remediation`
workflow for ArgoCD-managed namespaces by checking for the
`argocd.argoproj.io/managed-by` annotation. The GitOps adapter
(`examples/adapters/gitops/`) uses the specialized `gitops-remediation`
workflow with automated PR creation.

See also: guides/adapters.md (workflow selection), architecture/phases.md (AwaitingSync), examples/acs.md (ACS GitOps variant)
