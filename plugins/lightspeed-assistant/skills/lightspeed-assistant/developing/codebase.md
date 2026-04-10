# Codebase Map

## GitHub Organization

All repos live in **[NotAKubeKlaw](https://github.com/NotAKubeKlaw)**.

## Repositories

| Repo | Language | Purpose |
|------|----------|---------|
| `lightspeed-operator/` | Go | Operator: CRDs, reconciler, webhooks, RBAC |
| `lightspeed-agent/` | TypeScript | Agent: Claude SDK + Fastify, chat SSE |
| `lightspeed-console/` | React/TS | Console plugin: proposal UI, chat |
| `lightspeed-skills/` | Mixed | Per-profile skills OCI images |
| `lightspeed-gitops-demo/` | YAML | GitOps demo: ArgoCD-managed workloads for proposals |

## Key Files (operator — proposal system)

### CRD Types (`api/v1alpha1/`)
- `lightspeedproposal_types.go` — Proposal CRD: phases, step statuses, results
- `workflow_types.go` — OlsWorkflow CRD: 3 steps, skip support
- `agent_types.go` — OlsAgent CRD: LLM + skills + prompt
- `llmprovider_types.go` — OlsLlmProvider CRD: provider type, model, creds

### Reconciler (`internal/controller/proposal/`)
- `reconciler.go` — Main reconciler: phase handlers, callAgent, retry, escalation
- `rbac.go` — Per-proposal RBAC creation and cleanup
- `resolve.go` — Workflow CR resolution, per-proposal overrides
- `client.go` — REST client to agent API
- `response_types.go` — Agent response wrapper types
- `schemas.go` — JSON schema validation for agent outputs
- `sandbox.go` — Sandbox lifecycle (claim, wait)
- `sandbox_templates.go` — SandboxTemplate management (ensure, reconcile)

### Adapter Examples (`examples/adapters/`)
Each adapter is self-contained: code, skills, Containerfile, deploy script.
- `acs/` — ACS violation webhook → proposals (image vulnerability remediation)
- `alertmanager/` — AlertManager webhook → proposals (JVM OOMKill demo)
- `custom-components/` — Demonstrates adapter-defined structured output (custom `components` in agent responses rendered by console)
- `gitops/` — GitOps-aware remediation (ArgoCD/OSSM integration)
- `mco-advisory/` — MCO diagnostics: advisory-only adapter for MachineConfigPool degradation (custom outputSchema, no execution)
- `ossm/` — OpenShift Service Mesh adapter
- `upgrade/` — Cluster upgrade trigger

### Setup CRs (`examples/setup/`)
- `00-system-prompts.yaml` — System prompt ConfigMaps
- `01-llm-providers.yaml` — LLM provider CRs
- `02-agents.yaml` — Agent CRs
- `03-workflows.yaml` — Core workflow CRs (remediation, advisory, gitops, trust-mode, upgrade)
- `04-proposals.yaml` — Example proposal CRs
- `05-acs-workflow.yaml` — ACS-specific agents, prompts, workflows
- `06-alertmanager-workflow.yaml` — AlertManager-specific workflows
- `07-ossm-workflow.yaml` — Service Mesh workflows
- `08-gitops-workflow.yaml` — GitOps remediation workflows
- `09-gitops-advisory-workflow.yaml` — GitOps advisory-only workflows

## What's Legacy (ignore these)

- `internal/controller/appserver/` — Old backend, superseded by proposal flow
- `internal/controller/olsconfig_controller.go` — Legacy OLSConfig orchestrator
- `lightspeed-service/` — Old Python service, not used by proposals

## What's New (focus here)

- `internal/controller/proposal/` — The proposal reconciler
- `api/v1alpha1/*proposal*|*workflow*|*agent*|*llmprovider*` — The 4 CRDs
- `examples/` — Adapter examples, setup CRs, and this documentation

See also: developing/reconciler.md, developing/deploying.md
