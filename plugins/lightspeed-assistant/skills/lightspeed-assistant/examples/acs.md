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

## ACS-Specific Agents and Workflows

```yaml
# ACS analyzer agent — uses ACS-specific skills image
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
# ACS remediation workflow
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
    agent: verifier
```

Workflow definitions are in `examples/setup/05-acs-workflow.yaml`.

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
