# Example: ACS Violation Pipeline

Red Hat Advanced Cluster Security (RHACS/ACS) detects policy violations
and sends webhooks that create LightspeedProposals automatically.

## Architecture

```
ACS Central → webhook → ACS Adapter → LightspeedProposal
                        (examples/adapters/acs/)    ↓
                                              Operator reconciles
```

The ACS adapter is a standalone binary in `examples/adapters/acs/`.
It receives ACS violation webhooks and creates proposals.

> **Confirm before applying.** ACS setup involves creating resources and
> configuring webhooks. Ask the user for confirmation before each step.

## Quick Start

```bash
KUBECONFIG=/path/to/kubeconfig bash examples/adapters/acs/deploy.sh
```

This deploys the adapter, builds the skills image, creates agents,
workflows, and configures the ACS notifier.

## ACS-Specific Skills

The adapter includes its own skills in `examples/adapters/acs/skills/`:
- **acs-image-scanner** — scan container images for CVEs
- **cluster-ops** — cluster remediation operations
- **platform-docs** — OpenShift/K8s documentation
- **rbac-security** — minimum-privilege RBAC mapping
- **redhat-support** — Red Hat knowledge base and Jira

## ACS-Specific Agents

```yaml
# ACS analyzer — security-focused analysis with ACS skills
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: acs-analyzer
spec:
  llm: smart
  skills:
    image: <registry>/acs-skills:latest
  systemPromptRef:
    name: acs-analysis-prompt
---
# ACS GitOps analyzer — advises git changes instead of cluster changes
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: acs-gitops-analyzer
spec:
  llm: smart
  skills:
    image: <registry>/acs-skills:latest
  systemPromptRef:
    name: acs-gitops-analysis-prompt   # tells agent NOT to propose cluster changes
---
# ACS executor and verifier — use ACS skills image for post-fix scanning
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: acs-executor
spec:
  llm: fast
  skills:
    image: <registry>/acs-skills:latest
  systemPromptRef:
    name: execution-prompt             # reuses standard execution prompt
---
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: acs-verifier
spec:
  llm: fast
  skills:
    image: <registry>/acs-skills:latest
  systemPromptRef:
    name: verification-prompt          # reuses standard verification prompt
```

Four agents because the adapter selects a workflow based on whether
the target namespace is GitOps-managed. The `acs-gitops-analyzer` uses
a prompt that describes changes as YAML diffs instead of `oc` commands.

## ACS Workflow Variants

Three workflows handle the different ACS remediation patterns.
Definitions are in `examples/setup/05-acs-workflow.yaml`.

```yaml
# 1. Full remediation — analyze vulnerability → execute fix → verify
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: acs-remediation
spec:
  analysis:
    agent: acs-analyzer
  execution:
    agent: acs-executor
  verification:
    agent: acs-verifier
---
# 2. GitOps remediation — analyze → advise git changes → user applies → verify
#    Used when the target namespace has the argocd.argoproj.io/managed-by annotation
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: acs-gitops-remediation
spec:
  analysis:
    agent: acs-gitops-analyzer   # advises git changes, not cluster changes
  execution:
    skip: true                   # user applies via git commit + ArgoCD sync
  verification:
    agent: acs-verifier
---
# 3. Advisory only — analyze ACS violation, no action
#    Used for runtime anomalies or audit-only policies
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: acs-advisory
spec:
  analysis:
    agent: acs-analyzer
  execution:
    skip: true
  verification:
    skip: true
```

The adapter auto-selects the workflow:
- **acs-remediation** for namespaces without GitOps
- **acs-gitops-remediation** for ArgoCD-managed namespaces
- **acs-advisory** for runtime anomaly policies (investigation only)

## Adapter Features

- **Namespace filtering:** `--allowed-namespaces` flag restricts which namespaces create proposals
- **Phase-aware dedup:** Won't create a proposal if one already exists for the same violation
- **Cooldown:** Configurable interval between proposals for the same alert

## Testing

```bash
# Deploy a vulnerable workload
oc apply -f hack/demo-acs-violation.yaml

# Fire a simulated ACS violation webhook (no ACS install needed)
KUBECONFIG=... bash hack/fire-acs-violation.sh
```

## Full Guide

See `examples/adapters/acs/CLAUDE.md` for complete ACS installation,
notifier setup, and troubleshooting.

See also: guides/adapters.md (building custom adapters), examples/remediation.md
